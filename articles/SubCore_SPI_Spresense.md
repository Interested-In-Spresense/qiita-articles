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

- [MainCore.ino](https://github.com/Interested-In-Spresense/sketches/blob/master/MultiCore/SubSPI/MainCore/MainCore.ino)
- [SubCore1.ino](https://github.com/Interested-In-Spresense/sketches/blob/master/MultiCore/SubSPI/SubCore1/SubCore1.ino)

以下では、SubCoreからSPIを使うためのポイントとなる部分を抜粋して説明します。

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

MainCoreは `MP.begin(SUBCORE_ID)` でSubCore1を起動し、`MP.Send()` で測距を要求します。SubCore1は要求を受け取ると、SPI5経由で取得した測距結果を `MP.Send()` で返します。

```cpp
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
