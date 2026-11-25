# SpresenseのSubCoreからSPIを使ってみる！

## 初めに

Spresenseの魅力の一つは、やっぱりマルチコアだと思っています。

最近、LLMにSpresenseのことを聞いていると、SubCoreからSPIを使うことができない、という回答が返ってきました。

以前からLCDやマルチIMUなど、SubCoreからSPIを使う例があるので、ちょっと不思議に思いました。

ということで、SubCoreからSPIを使うための、できるだけシンプルなサンプルを作成してみました。

## 使用したもの

- Spresense
- Spresense拡張ボード
- MM-ToF10アドオンボード
- SDカード（ログ記録用）
- [MM-ToF10ライブラリ](https://github.com/Interested-In-Spresense/MM-ToF10)
- Arduino IDE
- Spresense Arduinoボードパッケージ

## ブログ（元ネタ）

- [SubCoreでSPIを読んでみる](https://spresense.livedoor.blog/archives/40645090.html)

## SubCoreからSPIを使ってみる

SpresenseではMainCoreだけでなく、SubCoreからもSPIを使うことができます。

センサーの読み出しをSubCoreに任せることで、MainCoreで別の処理を行うような構成も考えられます。

今回は、複雑なアプリケーションを作るのではなく、SubCoreからSPIを操作する部分を切り出したサンプルを作成しました。

## 今回の構成

今回はMM-ToF10をSubCore1からSPI5経由で操作し、測距結果をMainCoreに渡します。MainCoreではシリアル出力とSDカードへの記録を行います。

| Core | 役割 |
| --- | --- |
| MainCore | SubCore1の起動、測距要求、結果の受信、CSV記録 |
| SubCore1 | MM-ToF10の初期化、SPI5による測距、結果の返信 |

## サンプルコード

スケッチ一式はこちらです。

https://github.com/Interested-In-Spresense/sketches/tree/master/MultiCore/SubSPI

### MainCore側

```cpp
/*
 *  MainCore.ino - SubSPI Example using MM-ToF10 (MainCore)
 *
 *  Launches SubCore1 which reads ToF distance via SPI5 (MM-ToF10 add-on board).
 *  MainCore requests distance every 100 ms, prints to Serial, and logs to SD card.
 *
 *  SD card log file: /tof_log.csv
 *    columns: elapsed_ms, distance_mm
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 */

#ifdef SUBCORE
#error "Core selection is wrong!!"
#endif

#include <MP.h>
#include <SDHCI.h>

#define SUBCORE_ID        1
#define MSG_REQ_DISTANCE  10
#define MSG_RET_DISTANCE  11
#define LOG_FILENAME      "tof_log.csv"
#define TEST_DURATION_MS  10000

struct ToFData {
  float distance_mm;
};

SDClass SD;
File    logFile;
unsigned long startTime = 0;

void setup() {
  Serial.begin(115200);
  delay(500);  // non-blocking startup; avoid while(!Serial) stall

  // --- SD card ---
  if (!SD.begin()) {
    Serial.println("[Main] SD init failed — logging disabled");
  } else {
    // Append to existing file (or create new)
    logFile = SD.open(LOG_FILENAME, FILE_WRITE);
    if (logFile) {
      logFile.println("elapsed_ms,distance_mm");
      logFile.flush();
      Serial.print("[Main] Logging to ");
      Serial.println(LOG_FILENAME);
    } else {
      Serial.println("[Main] SD open failed — logging disabled");
    }
  }

  // --- SubCore ---
  MP.begin(SUBCORE_ID);
  MP.RecvTimeout(3000);

  startTime = millis();

  Serial.println("[Main] SubSPI MM-ToF10 sample started");
  Serial.println("elapsed_ms,distance_mm");
}

void loop() {
  // Check if test duration exceeded
  if (millis() - startTime > TEST_DURATION_MS) {
    if (logFile) {
      logFile.close();
      Serial.println("[Main] File closed after 10 seconds");
    }
    while (1) { delay(10); }  // Stop
  }

  // Request ToF distance from SubCore1
  int ret = MP.Send(MSG_REQ_DISTANCE, (uint32_t)0, SUBCORE_ID);
  if (ret < 0) {
    Serial.print("[Main] MP.Send failed: ");
    Serial.println(ret);
    return;
  }

  int8_t  msgid;
  ToFData *data = nullptr;

  if (MP.Recv(&msgid, &data, SUBCORE_ID) >= 0
      && msgid == MSG_RET_DISTANCE && data != nullptr) {

    unsigned long t = millis();

    // Serial output
    Serial.print(t);
    Serial.print(',');
    Serial.println(data->distance_mm, 1);

    // SD card output
    if (logFile) {
      logFile.print(t);
      logFile.print(',');
      logFile.println(data->distance_mm, 1);
      logFile.flush();
    }
  } else {
    Serial.println("[Main] No data received");
  }
}
```

### SubCore1側

```cpp
/*
 *  SubCore1.ino - MultiCore SPI Example using MM-ToF10 (SubCore1)
 *
 *  Reads ToF distance via SPI5 using the MM-ToF10 library and sends
 *  1D distance data (mm) to MainCore on request.
 *
 *  Hardware: MM-ToF10 add-on board connected to Spresense extension board.
 *  Library : https://github.com/Interested-In-Spresense/MM-ToF10
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 */

#if (SUBCORE != 1)
#error "Core selection is wrong!!"
#endif

#include <MP.h>
#include <MM-TOF10.h>

#define MSG_REQ_DISTANCE  10
#define MSG_RET_DISTANCE  11

// Shared result buffer (SubCore static → MainCore reads via MP pointer)
struct ToFData {
  float distance_mm;
};
static ToFData tofBuf;

// ---- Setup -------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  // Initialize MM-ToF10 (uses SPI5 internally)
  MMToF10.begin();
  MMToF10.sync();
  MMToF10.nomal(ShortDistance, LowSpeed);

  MP.begin();
  MP.RecvTimeout(3000);
  Serial.println("[Sub1] MM-ToF10 ready");
}

// ---- Loop --------------------------------------------------------------
void loop() {
  int8_t msgid;
  uint32_t dummy;

  if (MP.Recv(&msgid, &dummy) >= 0 && msgid == MSG_REQ_DISTANCE) {
    tofBuf.distance_mm = MMToF10.get1d();

    Serial.print("[Sub1] dist=");
    Serial.print(tofBuf.distance_mm, 1);
    Serial.println(" mm");
    Serial.flush();

    MP.Send(MSG_RET_DISTANCE, &tofBuf);

  } else {
    Serial.println("[Sub1] recv timeout");
  }
}
```

## コードの説明

### SubCoreからSPI5を使う

今回のポイントは、以下の処理をMainCoreではなくSubCore1で実行しているところです。

```cpp
MMToF10.begin();
MMToF10.sync();
MMToF10.nomal(ShortDistance, LowSpeed);
```

MM-ToF10の初期化、同期、短距離・低速モードの設定を行っています。SPI5の操作はMM-ToF10ライブラリの内部で行われるので、スケッチにはSPI.begin()やSPI.transfer()は直接出てきません。測距結果の取得もSubCore1で行います。

```cpp
tofBuf.distance_mm = MMToF10.get1d();
```

このように、SPIを使ったセンサーの処理をSubCore側にまとめています。MainCore側ではMM-ToF10ライブラリをインクルードする必要もありません。

### MainCoreとのデータの受け渡し

MainCoreは `MP.begin(SUBCORE_ID)` でSubCore1を起動し、`MP.Send()` で測距を要求します。SubCore1は要求を受け取ると、SPI5経由で測距データを取得し、次の処理で結果を返します。

```cpp
tofBuf.distance_mm = MMToF10.get1d();
MP.Send(MSG_RET_DISTANCE, &tofBuf);
```

MainCoreは `MP.Recv()` で構造体のポインタを受け取り、距離をシリアルモニタとSDカードに出力します。つまり、MainCoreはSPIを操作せず、SubCore1で取得した測距結果だけを受け取る構成です。

## 実行方法

1. Spresense拡張ボードにMM-ToF10を接続し、ログを取る場合はSDカードを挿入します。
2. Arduino IDEにMM-ToF10ライブラリを導入します。
3. SubCore1.inoを開き、Coreの選択をSubCore 1にして書き込みます。
4. MainCore.inoを開き、Coreの選択をMainCoreにして書き込みます。
5. シリアルモニタを115200bpsで開きます。

正常に動作すると、MainCoreから時刻と距離がCSV形式で出力され、SubCore1からも距離のデバッグ出力が行われます。SDカードの初期化とファイルのオープンに成功していれば、測距結果は `tof_log.csv` に記録されます。

## 関連記事

Spresenseのマルチコアを使ったセンサーの読み出しについては、こちらでも試しています。

- [SpresenseのそれぞれのCoreからそれぞれのセンサーを読み出してみる！](https://qiita.com/Interested_in_Spresense/items/73d174b05751529a69e6)
- [Spresense マルチIMUとその他のセンサーの共存](https://qiita.com/Interested_in_Spresense/items/b11d7276dd09eea2defe)

## 所感

LLMは便利なんですが、公式サイトにサンプルがないからといって、できないとは限らないんですよね。

Spresenseのような環境では、実際に使えるサンプルを残しておくことも大事だなあと思っています。

SubCoreでSPIを使いたい方の参考になれば幸いです。
