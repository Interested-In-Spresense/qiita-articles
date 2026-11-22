# qiita-articles

ChatGPTで整理した技術記事をMarkdownで管理し、**GitHub ActionsからQiita APIへ手動投稿**する実験用リポジトリです。

ブログ「[SPRESENSEに興味あり](https://spresense.livedoor.blog/)」に書いた試行錯誤を元に、Qiita「[Interested_in_Spresense](https://qiita.com/Interested_in_Spresense)」向けの記事を作成します。

## 方針

- **ブログが先、Qiitaが後**：ブログには開発経緯、Qiitaには技術情報を整理して掲載
- GitHub Actionsは**手動実行のみ**。pushしただけでは投稿されません
- 最初はQiitaの**限定共有記事**として登録し、内容を確認してからQiita上で公開
- `create` と `update` を明示的に選択。更新には既存記事のIDが必要
- QiitaアクセストークンはGitHub Actions Secretsに保存し、ファイルやログに記載しない

> [!NOTE]
> **Information**
>
> このリポジトリは、Qiitaへの自動投稿の仕組みを共有するために、あえてPublicで公開しています。
>
> この仕組みを利用される場合は、必要に応じてリポジトリをPrivateに設定するなど、ご自身の運用方針に合わせて設定を変更してお使いください。
>
> QiitaのAPIトークンなどの認証情報は、リポジトリに直接記載せず、GitHub Secretsで管理してください。

## ファイル構成

```text
qiita-articles/
├── README.md
├── articles/
│   ├── ADXL335_Spresense.md
│   └── SubCore_SPI_Spresense.md
├── scripts/
│   └── publish.py
└── .github/
    └── workflows/
        └── publish.yml
```

## 初期設定

1. Qiitaの設定画面からAPIアクセストークンを発行します。記事の作成・更新に必要な `write_qiita` スコープを付与します。
2. GitHubリポジトリの **Settings → Secrets and variables → Actions → New repository secret** を開きます。
3. 名前を `QIITA_TOKEN` としてトークンを保存します。**トークンはREADME、記事、Issue、チャットなどに貼り付けないでください。**
4. `articles/` の記事を確認し、`【公開前に追記】` の部分を実際の情報で埋めます。サンプルコード・配線・測定条件を検証してから投稿してください。未完成の原稿はスクリプトが投稿を拒否します。

## 投稿方法

1. GitHubの **Actions** タブで **Publish to Qiita (manual)** を選択します。
2. **Run workflow** を押します。
3. `article` で記事を選びます。
4. 初回は `operation = create`、`item_id` は空欄で実行します。
5. 実行結果の **Job summary** またはログに表示される **Qiita Item ID** とURLを控えます。
6. Qiita上で内容を確認します。公開範囲の変更はQiita上で行ってください。

### 既存記事の更新

同じ記事を修正する場合は `operation = update` に切り替え、初回投稿で取得した `item_id` を入力します。**`create` を再実行すると重複記事が作成されます。**

> [!IMPORTANT]
> スクリプトはQiita APIのリクエストに `private: true` を指定しています。更新時も限定共有を指定するため、**公開済み記事の更新に使うと公開範囲が変わる可能性があります**。公開後の記事は、運用を見直すまではQiita上で直接修正してください。

## 記事の出典

- ADXL335：[その1](https://spresense.livedoor.blog/archives/40595400.html) / [その2](https://spresense.livedoor.blog/archives/40816718.html)
- SubCore SPI：[SubCoreでSPIを読んでみる](https://spresense.livedoor.blog/archives/40645090.html)

## 注意事項

- 現段階では構成を用意しただけで、**Qiita APIへの実投稿は未検証**です。
- 記事のタイトルとタグは `scripts/publish.py` の `ARTICLES` で管理しています。
- 原稿は元ブログをもとにした下書きです。未確認のコードや測定条件を埋めずに公開しないでください。

## 今後やりたいこと

Qiitaへの初回投稿を検証し、実行結果やハマった点をブログにまとめる予定です。
