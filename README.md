# YouTube コメント分析ダッシュボード
## 目的
YouTube に投稿された自社製品や他社製品の動画に対するコメント（消費者の声）を分析することで、商品開発やブランドイメージの向上に活用する。  

## アーキテクチャ
### ハイレベルアーキテクチャ
<img width="1440" alt="image" src="https://github.com/gtagheuer/youtube-comment-analysis/assets/653609/ab98c8ff-40d7-4425-84a0-8ac0d33e3713">

### 詳細アーキテクチャ
<img width="1440" alt="image" src="https://github.com/gtagheuer/youtube-comment-analysis/assets/653609/130f1137-5a71-46b3-8db4-9913532fd8df">

## 完成イメージ図
<img width="1314" alt="image" src="https://github.com/gtagheuer/youtube-comment-analysis/assets/653609/c1d39266-a822-42ba-b45b-6e08c2008dc6">

## 注意
本プロジェクトでは Google Cloud の製品を利用するので料金が掛かります。  
費用の大半はコメントの感情分析を行う Cloud Natural Language API です。  
1コメントの分析に 0.0001 USD 掛かるので、たとえば 10,000 コメント分析すると約 10 USD 掛かります。
## 実作業
### Google Cloud の下準備
1. まずは、Google Cloud (https://www.console.cloud.google.com) にアクセスし、新しい Project を作成しましょう。
2. ページ上部のドロップダウンボタンから新しく作成した Project に切り替えましょう。
   <details>
      <summary><strong>💡 Tips - Project</strong></summary>
      Google Cloud では...
   </details>
3. 右上のターミナルのようなアイコンをクリックして Cloud Shell を起動しましょう。
   - Cloud Shell は〜〜〜〜
4. 下記のコマンドを実行することで、現在の Project ID を表示することができます。
   ```shell
   gcloud config get-value project
   ```
   Project ID を表示するのにいちいち上のコマンドを叩くのは面倒なので `PROJECT_ID` という環境変数に保存しておきましょう。
   ```shell
   export PROJECT_ID=$(gcloud config get-value project)
   ```
   保存できたか確認するために、以下のコマンドを実行してください。  
   `$PROJECT_ID` の部分がきちんと置き換わって表示されていれば保存されています。
   ```shell
   echo $PROJECT_ID
   ```
5. 現在の Cloud Shell 上でのディレクトリにどのようなファイルがあるか確認してみましょう。  
   下記のコマンドを実行してください。
   ```shell
   ls
   ```
   特にこれまでに何もしていなければ `README-cloudshell.txt` のみが表示されるはずです。
6. YouTube コメント分析ダッシュボードの作成に必要なファイルをダウンロードしましょう。  
   下記のコマンドを実行してください。
   ```shell
   git clone https://github.com/gtagheuer/youtube-comment-analysis
   ```
   ダウンロードが終わった後に先程の `ls` コマンドを打ってみましょう。  
   新たに `youtube-comment-analysis` というディレクトリが見えているはずです。  
   今後はこのディレクトリで作業するので、そちらに移動しましょう。
   下記のコマンドを実行してください。
   ```shell
   cd youtube-comment-analysis
   ```
   もう一度 `ls` してみましょう。  
   今度はたくさんのファイルやフォルダが見えるはずです。
7. 最後に今回使用する API の有効化をしておきましょう。  
   下記のコマンドを実行してください。  
   ポップアップが表示された場合には「承認」してください。
   ```shell
   gcloud services enable \
          cloudbuild.googleapis.com \
          cloudfunctions.googleapis.com \
          eventarc.googleapis.com \
          run.googleapis.com \
          cloudscheduler.googleapis.com \
          logging.googleapis.com \
          pubsub.googleapis.com \
          bigquery.googleapis.com \
          language.googleapis.com \
          aiplatform.googleapis.com
   ```
8. 下準備はこれで終了です。  
   次のセクションからは Google Cloud で実際にいろいろなプロダクト（リソース）を作成していきます。

### リソース作成
---
#### BigQuery
1. BigQuery の細かい話に移る前に、本プロジェクトで最終的に完成させたい Table のスキーマをご覧ください。  
   カスタマイズしたい場合は `table_schema` ディレクトリに入っている各 JSON ファイルを修正してください。  
   **Product**
   | フィールド名    | データ型 |
   |:--------------|:--------|
   | product_id    | STRING  |
   | product_name  | STRING  |
   | product_group | STRING  |
   | region_code   | STRING  |
   ---
   **Video**
   | フィールド名           | データ型      |
   |:---------------------|:-------------|
   | product_id           | STRING       |
   | product_name         | STRING       |
   | product_group        | STRING       |
   | video_id             | STRING       |
   | video_url            | STRING       |
   | video_published_at   | TIMESTAMP    |
   | video_title          | STRING       |
   | video_description    | STRING       |
   | video_thumbnail_url  | STRING       |
   | video_view_count     | INTEGER      |
   | video_like_count     | INTEGER      |
   | video_favorite_count | INTEGER      |
   | video_comment_count  | INTEGER      |
   | video_channel_id     | STRING       |
   | video_channel_title  | STRING       |
   | region_code          | STRING       |
   ---
   **Comment**
   | フィールド名                  | データ型      |
   |:----------------------------|:-------------|
   | product_id                  | STRING       |
   | product_name                | STRING       |
   | product_group               | STRING       |
   | video_id                    | STRING       |
   | comment_id                  | STRING       |
   | comment_published_at        | TIMESTAMP    |
   | comment_author_name         | STRING       |
   | comment_author_image_url    | STRING       |
   | comment_like_count          | INTEGER      |
   | comment_text                | STRING       |
   | comment_sentiment           | STRING       |
   | comment_sentiment_score     | FLOAT        |
   | comment_sentiment_magnitude | FLOAT        |
   | region_code                 | STRING       |
   ---
   **Summary**
   | フィールド名                  | データ型      |
   |:----------------------------|:-------------|
   | product_id                  | STRING       |
   | product_name                | STRING       |
   | product_group               | STRING       |
   | summary_text                | STRING       |
   | region_code                 | STRING       |


2. BigQuery は Project > Dataset > Table というデータ構造になっています。  
   現在は Project のみ作成している状態なので Dataset と Table を作成していきます。  
   下記のコマンドを実行して `youtube` という Dataset を作成してください。
   ```shell
   bq mk --dataset\
      --location=asia-northeast1 \
      $PROJECT_ID:youtube
   ```
   本コマンドでは `--location` オプションで `asia-northeast1` （東京リージョン）を指定していますが、[こちらのページ](https://cloud.google.com/storage/docs/locations?hl=ja)を参考にして、必要に応じて修正してください。  
   たとえば、`US` （米国マルチリージョン）等もお選びいただけます。
3. 次に Table を作成していきます。  
   下記のコマンドを順番に実行してください。  
   **Product Table の作成**
   ```shell
   bq mk --table\
      --location=asia-northeast1 \
      $PROJECT_ID:youtube.product \
      table_schema/product_table_schema.json
   ```
   **Video Table の作成**
   ```shell
   bq mk --table \
      --location=asia-northeast1 \
      --time_partitioning_type=MONTH \
      $PROJECT_ID:youtube.video \
      table_schema/video_table_schema.json
   ```
   **Comment Table の作成**
   ```shell
   bq mk --table \
      --location=asia-northeast1 \
      --time_partitioning_type=MONTH \
      $PROJECT_ID:youtube.comment \
      table_schema/comment_table_schema.json
   ```
   （注意：上記コマンドは「Google Cloud の下準備」の6番のステップで `git clone` したディレクトリに移動していることが前提のコードになっています。`cd` コマンドで `XXX` ディレクトリに移動しているかご確認ください。）  
4. Product Table に YouTube でコメント分析したい製品のデータをロードします。  
   サンプルファイル `product.csv` では Google 製品の名前になっていますが、自社製品に置き換えて実行してください。
   - Cloud Shell 上で直接編集する場合は Open Editor ボタンから編集して下さい。（エディタの起動に時間がかかります）
   - ローカル端末に CSV が存在する場合は Cloud Shell 右上の三点リーダ（︙）からファイルを Upload していただけます。
     - ファイル名を `product.csv` にしておき、アップロード先に table_data ディレクトリを選んでいただくと、ファイルを上書きできるので、以降のコードをそのままコピペ可能です。
     - もし、別のファイル名をお使いの場合は以降のコードで `product.csv` となっている部分を適宜修正して下さい。
   準備ができたら、下記のコマンドを実行してください。
   ```shell
   bq load \
      --source_format=CSV \
      $PROJECT_ID:youtube.product \
      table_data/product.csv 
   ```
5. 以上で BigQuery の準備は完了です。
---
#### IAM (Identity and Access Management)
1. Google Cloud では IAM を使って、リソースへのアクセス制限を実現します。  
   今回作成する YouTube コメント分析ダッシュボードには BigQuery や Cloud Functions といったリソースが含まれています。  
   認証されたユーザーやサービスだけがこれらのリソースにアクセスできるよう必要な IAM を整備していきます。  
2. Cloud Functions で使用するサービスアカウントを作成します。  
   下記のコマンドを実行してください。   
   ```shell
   gcloud iam service-accounts create cloud-functions-sa \
          --description="Service account for Cloud Functions in YouTube comment analysis project" \
          --display-name="Cloud Functions service account"
   ```
3. 次に Cloud Functions に必要な以下の権限をサービスアカウントに付与します。
   - BigQuery Admin
   - Pub/Sub Publisher  

   `add-iam-policy-binding` コマンドは1つの `role` しか追加できないので、それぞれの `role` について実行します。
   ```shell
   gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:cloud-functions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
          --role="roles/bigquery.admin"
   ```
   ```shell
   gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:cloud-functions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
          --role="roles/pubsub.publisher"
   ```
   ```shell
   gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:cloud-functions-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
          --role="roles/pubsub.subscriber"
   ```

4. Pub/Sub で使用するサービスアカウントを作成します。
   下記のコマンドを実行してください。   
   ```shell
   gcloud iam service-accounts create pubsub-sa \
          --description="Service account for Pub/Sub in YouTube comment analysis project" \
          --display-name="Pub/Sub service account"
   ```
5. 次に Pub/Sub に必要な以下の権限をサービスアカウントに付与します。
   - Cloud Run Invoker
   - Service Account Token Creator  
   
   `add-iam-policy-binding` コマンドは1つの `role` しか追加できないので、それぞれの `role` について実行します。
   ```shell
   gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:pubsub-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
          --role="roles/run.invoker"
   ```
   ```shell
   gcloud projects add-iam-policy-binding $PROJECT_ID \
          --member="serviceAccount:pubsub-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
          --role="roles/iam.serviceAccountTokenCreator"
   ```
6. たぶん Vertex AI の感情分析でも必要な権限があるので、あとで追加する
   XXXXXX
7. 以上で IAM の準備は完了です。
---
#### YouTube Data API
1. YouTube Data API を有効化します。
   ```shell
   gcloud services enable youtube.googleapis.com
   ```
2. API Key を発行します。
   ```shell
   gcloud beta services api-keys create --display-name="YouTube Data API Key"
   ```
3. このままだと、この API Key はあらゆる API 呼び出しに使うことができ、非常に危険です。  
   YouTube Data API の呼び出しにだけ使えるように制限しましょう。  
   まずは以下のコマンドを実行して API Key の Key ID を環境変数 `KEY_ID` に格納します。
   ```shell
   export KEY_ID=$(gcloud services api-keys list | grep uid: | awk '{print $2}')
   ```
   次に API Key が使用できる API を YouTube Data API のみに制限します。
   ```shell
   gcloud beta services api-keys update $KEY_ID \
   --api-target=service=youtube.googleapis.com
   ```
4. 上のステップでは API Key の Key ID を環境変数 `KEY_ID` に格納しましたが  
   実際に API Key を使って YouTube Data API を呼び出すには `keyString` が必要です。  
   以下のコマンドを実行して API Key の `keyString` を環境変数 `YOUTUBE_API_KEY` に格納します。  
   ```shell
   export YOUTUBE_API_KEY=$(gcloud alpha services api-keys get-key-string $KEY_ID | awk '{print $2}')
   ```
   上記コマンドには alpha バージョンのコマンドが含まれていますので、うまく動作しない可能性があります。  
   - その場合は [API 管理画面](https://console.cloud.google.com/apis/credentials)で `SHOW KEY` をクリックして `Your API key` の部分に表示されている文字列をコピーして、環境変数 `YOUTUBE_API_KEY` に格納してください。
     ```shell
     export YOUTUBE_API_KEY=コピーしてきた keyString の文字列
     ```
5. 以上で YouTube Data API の準備は完了です。
---
#### Pub/Sub
1. 本プロジェクトで必要な Pub/Sub トピックを作成します。  
   少し時間がかかりますが、一気に6つ作成します。
   ```shell
   gcloud pubsub topics create trigger
   gcloud pubsub topics create product
   gcloud pubsub topics create video
   gcloud pubsub topics create comment
   gcloud pubsub topics create sentiment
   gcloud pubsub topics create analysis
   ```
2. comment トピックは Pull 形式の Subscription を作成します。  
   今回 Pull 形式の Subscription は comment トピックのみで、他の5つのトピックは全て Push 形式です。
   ```shell
   gcloud pubsub subscriptions create comment-sub \
          --topic=comment \
          --ack-deadline=120
   ```
   <details>
      <summary><strong>💡 Tips - Pull / Push Subscription</strong></summary>
      Google Cloud では...
   </details>
3. 以上で Pub/Sub の準備は完了です。
---
#### Cloud Functions
1. Pub/Sub でトリガーできる Cloud Functions を作成します。  
   下記コマンドでは `--gen2` オプションが指定されているため、第１世代に比べて高パフォーマンスな第２世代がデプロイされます。  
   第２世代は実際には裏側では Cloud Run が動いており、IAM のステップ5で Pub/Sub 用のサービスアカウントを作成した際に Cloud Run を呼び出せるロール（roles/run.invoker）を付与していたのはそのためです。  
   本プロジェクトでは6つの Cloud Functions を使用するので、以下の6つのコマンドを実行しますが、1つ1つがそれなりに時間が掛かり、実行が終わるたびにコピペするのが大変なので全てをまとめたコマンドを以下に用意しました。  
   完了までに5分〜10分ほど掛かります。
   ```shell
   gcloud functions deploy get_product --gen2 --runtime python311 --region asia-northeast1 --source functions/get_product_function --entry-point load_data --trigger-topic trigger --memory 1024MB --timeout 540 --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-location asia-northeast1 --set-env-vars PROJECT_ID=$PROJECT_ID
   gcloud functions deploy search_video --gen2 --runtime python311 --region asia-northeast1 --source functions/search_video_function --entry-point load_data --trigger-topic product --memory 1024MB --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-location asia-northeast1 --set-env-vars PROJECT_ID=$PROJECT_ID,YOUTUBE_API_KEY=$YOUTUBE_API_KEY
   gcloud functions deploy search_comment --gen2 --runtime python311 --region asia-northeast1 --source functions/search_comment_function --entry-point load_data --trigger-topic video --memory 1024MB --max-instances 150 --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-location asia-northeast1 --set-env-vars PROJECT_ID=$PROJECT_ID,YOUTUBE_API_KEY=$YOUTUBE_API_KEY
   gcloud functions deploy analyze_sentiment --gen2 --runtime python311 --region asia-northeast1 --source functions/analyze_sentiment_function --entry-point load_data --trigger-topic analysis --memory 1024MB --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-location asia-northeast1 --set-env-vars PROJECT_ID=$PROJECT_ID
   gcloud functions deploy insert_video --gen2 --runtime python311 --region asia-northeast1 --source functions/insert_video_function --entry-point load_data --trigger-topic video --memory 1024MB --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-location asia-northeast1 --set-env-vars PROJECT_ID=$PROJECT_ID
   gcloud functions deploy insert_comment --gen2 --runtime python311 --region asia-northeast1 --source functions/insert_comment_function --entry-point load_data --trigger-topic sentiment --memory 1024MB --max-instances 150 --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com --trigger-location asia-northeast1 --set-env-vars PROJECT_ID=$PROJECT_ID
   ```
   上記のコマンドを実行した場合には、以下の6つのコマンドは実行する必要はありません。  
   **Get Product Function**
   ```shell
   gcloud functions deploy get_product \
          --gen2 \
          --runtime python311 \
          --region asia-northeast1 \
          --source functions/get_product_function \
          --entry-point load_data \
          --trigger-topic trigger \
          --memory 1024MB \
          --timeout 540 \
          --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-location asia-northeast1 \
          --set-env-vars PROJECT_ID=$PROJECT_ID
   ```
   **Search Video Function**
   ```shell
   gcloud functions deploy search_video \
          --gen2 \
          --runtime python311 \
          --region asia-northeast1 \
          --source functions/search_video_function \
          --entry-point load_data \
          --trigger-topic product \
          --memory 1024MB \
          --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-location asia-northeast1 \
          --set-env-vars PROJECT_ID=$PROJECT_ID,YOUTUBE_API_KEY=$YOUTUBE_API_KEY
   ```
   **Search Comment Function**
   ```shell
   gcloud functions deploy search_comment \
          --gen2 \
          --runtime python311 \
          --region asia-northeast1 \
          --source functions/search_comment_function \
          --entry-point load_data \
          --trigger-topic video \
          --memory 1024MB \
          --max-instances 150 \
          --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-location asia-northeast1 \
          --set-env-vars PROJECT_ID=$PROJECT_ID,YOUTUBE_API_KEY=$YOUTUBE_API_KEY
   ```
   **Analyze Sentiment Function**
   ```shell
   gcloud functions deploy analyze_sentiment \
          --gen2 \
          --runtime python311 \
          --region asia-northeast1 \
          --source functions/analyze_sentiment_function \
          --entry-point load_data \
          --trigger-topic analysis \
          --memory 1024MB \
          --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-location asia-northeast1 \
          --set-env-vars PROJECT_ID=$PROJECT_ID
   ```
   **Insert Video Function**
   ```shell
   gcloud functions deploy insert_video \
          --gen2 \
          --runtime python311 \
          --region asia-northeast1 \
          --source functions/insert_video_function \
          --entry-point load_data \
          --trigger-topic video \
          --memory 1024MB \
          --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-location asia-northeast1 \
          --set-env-vars PROJECT_ID=$PROJECT_ID
   ```
   **Insert Comment Function**
   ```shell
   gcloud functions deploy insert_comment \
          --gen2 \
          --runtime python311 \
          --region asia-northeast1 \
          --source functions/insert_comment_function \
          --entry-point load_data \
          --trigger-topic sentiment \
          --memory 1024MB \
          --max-instances 150 \
          --run-service-account cloud-functions-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-service-account pubsub-sa@$PROJECT_ID.iam.gserviceaccount.com \
          --trigger-location asia-northeast1 \
          --set-env-vars PROJECT_ID=$PROJECT_ID
   ```
2. 以上で Cloud Functions の準備は完了です。
---
#### Cloud Scheduler
1. Get Product Function をトリガーする Pub/Sub を定期実行するために Cloud Scheduler を作成します。  
   月初から Product Table の `product_group` ごとに毎日18時に分析パイプラインを起動します。  
   今回は日本の自動車会社6社の製品を分析するので、6日間かけて1日ごとに1社ずつ分析します。  
   1社ごとに分ける理由は YouTube Data API の Quota がデフォルトでは1日に10,000ユニットだからです。  
   あくまで目安ですが、1製品につき 150-200 ユニット消費しますので、<u>**1社50製品以内**</u>にとどめて分析を行ってください。  
   <details>
      <summary><strong>💡 Tips - YouTube Data API Quota</strong></summary>
      Google Cloud では...
   </details>
2. 下記のコマンドを実行してください。
   折りたたみで拡張例を書く。
   ```shell
   gcloud scheduler jobs create pubsub trigger-job \
          --location=asia-northeast1 \
          --schedule="0 0 * * *" \
          --topic=trigger \
          --message-body='{"region_code": "JP"}' \
          --time-zone="Asia/Tokyo"
   ```
   本プロジェクトでは同一製品でも国によって名称や各言語での表記が違う可能性を考慮して Product Table で `region_code` 別に製品データを格納するようにしています。  
   YouTube Data API で動画の検索を行う際にも `region_code` は考慮されますので、上記のコマンドで `region_code` を `{Key: Value}` 形式でCloud Scheduler から Pub/Sub の `trigger` トピックに渡すことで一連の処理が連鎖的に開始されます。
3. Analyze Sentiment Function をトリガーする Pub/Sub を定期実行するために Cloud Scheduler を作成します。
4. 下記のコマンドを実行してください。
   ```shell
   gcloud scheduler jobs create pubsub analysis-job \
          --location=asia-northeast1 \
          --schedule="* 0-11 * * *" \
          --topic=analysis \
          --message-body="{\"language\": \"ja\"}" \
          --time-zone="Asia/Tokyo"
   ```
5. 以上で Cloud Scheduler の準備は完了です。
---


#### Product Table への行の追加
レコードを1行だけ追加したい場合、下記のコマンドを実行してください。
```sql
INSERT
      `yt-analysis-test.youtube.product`
      (product_id, product_name, product_group, region_code)
VALUES
      ('sample_id', 'sample_name', 'sample_group', 'sample_code');
```

レコードを複数行追加することもできます。
```sql
INSERT
      `yt-analysis-test.youtube.product`
      (product_id, product_name, product_group, region_code)
VALUES
      ('sample_id1', 'sample_name1', 'sample_group1', 'sample_code1'),
      ('sample_id2', 'sample_name2', 'sample_group2', 'sample_code2'),
      ('sample_id3', 'sample_name3', 'sample_group3', 'sample_code3');
```
