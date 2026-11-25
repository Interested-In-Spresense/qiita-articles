# ADXL335のSpresense用ドライバを作ってみる！ ～アナログ入力の落とし穴～

## 初めに

Spresenseでアナログ出力の3軸加速度センサーADXL335を使うためのArduinoライブラリを作ってみました。衝撃検知にも使えるようにしたのですが、実際に読み出してみると想定した値が出ません。原因を調べると、拡張ボードの分圧回路が関係していました。

## 使用したもの

- Spresenseメインボード、拡張ボード
- ADXL335
- Arduino IDE

## ブログ（元ネタ）

- [ADXL335のSpresenseに合わせたドライバをつくってみる その1](https://spresense.livedoor.blog/archives/40595400.html)
- [ADXL335のSpresenseに合わせたドライバをつくってみる その2](https://spresense.livedoor.blog/archives/40816718.html)

## ADXL335のドライバを作る

ライブラリはこちらです。

https://github.com/Interested-In-Spresense/ADXL335

### 配線

今回は以下のように3軸を接続します。

| ADXL335 | Spresense拡張ボード |
|---|---|
| VCC | 3.3V |
| GND | GND |
| XOUT | A0 |
| YOUT | A1 |
| ZOUT | A2 |

### 加速度を読み出す

まずは3軸の加速度を読み出してみます。

```cpp
#include <ADXL335.h>
ADXL335 accel;

void setup() {
  Serial.begin(115200);
  accel.begin(A0, A1, A2);
}

void loop() {
  float x, y, z;
  accel.readG(x, y, z);
  Serial.print(x);
  Serial.print('\t');
  Serial.print(y);
  Serial.print('\t');
  Serial.println(z);
  delay(100);
}
```

2軸だけ使う場合は `accel.begin(A0, A1, -1);` と指定できます。未接続軸は0として扱われます。

### 衝撃検知

```cpp
#include <ADXL335.h>
ADXL335 accel;

void setup() {
  Serial.begin(115200);
  accel.begin(A0, A1, A2);
  accel.setShockThreshold(2.5f);
}

void loop() {
  float magnitude, x, y, z;
  if (accel.detectShock(magnitude, x, y, z)) {
    Serial.println(magnitude, 3);
  }
  delay(5);
}
```

加速度の合成値で判定するため、静止時の重力成分も含まれます。実際の衝撃検知ではサンプリング周期にも注意が必要です。

## 想定した値と違う！

3.3V駆動、0gで1.65V、感度330mV/gと仮定し、5Vフルスケールの10bit読み出しとして計算します。

| 条件 | 計算値（概算） | 実測値 |
|---|---:|---:|
| 0g | 338 | 約230 |
| +1g | 405 | 約270 |

## Spresense拡張ボードの分圧回路

CXD5602のADCに対して拡張ボードでは抵抗分圧を行っています。センサーの出力抵抗も分圧比に影響するため、単純な電圧換算では合わなくなります。

ADXL335の出力抵抗は32kΩで、Spresenseの拡張ボードの分圧抵抗は62kΩと10kΩです。

ADXL335の出力抵抗も含めて計算すると、ADCへの入力電圧は以下のようになります。

```
Vadc = 1.65 * 10 / (32 + 62 + 10)
     = 約0.159 V
```

## ADCのピンにも注意

調べてみると、A0/A1はLPADC、A4/A5はHPADCでした。ADC系統によって入力回路が異なるため、使用するピンにも注意が必要です。接続するピンを変えた場合は、改めてキャリブレーションを行います。

## キャリブレーションを入れてみる

各軸の0gと+1gのADC値を測って補正します。例えば次のように設定します。

```cpp
// キャリブレーション値の設定例
accel.setCalibration(230, 270,
                     228, 268,
                     232, 272);
```

変換式は `g = (raw - center) / (one_g - center)` です。10bitと12bitの値は混在させず、実際に使用する読み出し設定で測定します。

キャリブレーション用サンプルでは、Z、Y、Xの順に各軸が+1gとなる姿勢にしてシリアルモニタで操作します。他の軸の0g値と合わせて補正値を求め、flashの `adxl335_calib.txt` に保存します。次回起動時は保存値を読み込みます。

## サンプルコード

ライブラリには以下のサンプルスケッチも用意しています。

- [BasicRead.ino](https://github.com/Interested-In-Spresense/ADXL335/blob/main/examples/BasicRead/BasicRead.ino)：RAW値と加速度の表示
- [ShockDetect.ino](https://github.com/Interested-In-Spresense/ADXL335/blob/main/examples/ShockDetect/ShockDetect.ino)：衝撃検知
- [Calibration.ino](https://github.com/Interested-In-Spresense/ADXL335/blob/main/examples/Calibration/Calibration.ino)：対話式キャリブレーションと保存

## 所感

ADXL335のドライバを作るつもりが、Spresenseのアナログ入力回路まで調べることになりました。アナログセンサーを使う場合には、センサー側の出力インピーダンスと拡張ボードの入力回路を合わせて考える必要がありますね。

ということで、何かのお役に立てば！
