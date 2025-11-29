# GA4日別レポート抽出ツール (アクティブユーザー数とカスタムディメンション内訳)

このPythonスクリプトは、Google Analytics Data API (GA4) を使用し、指定した期間の日別アクティブユーザー数と、カスタム定義されたディメンション（言語など）ごとのイベント数をピボット形式のCSVファイルとして抽出します。

🚀 動作環境
Python 3.8以上
google-analytics-data クライアントライブラリ

📝 セットアップ手順
このツールを利用するには、以下の3つの主要なステップが必要です。

## ステップ 1: Google Cloud Platform (GCP) での認証設定

APIにアクセスするための「サービスアカウント」と「秘密鍵（JSONファイル）」を作成します。

### 1.プロジェクトの作成

Google Cloud Consoleにアクセスし、新しいプロジェクトを作成します。
ナビゲーションメニューから [IAM と管理] → [サービス アカウント] に移動します。
[サービス アカウントを作成] をクリックし、任意の名前（例: ga4-reporter）を付けて作成します。

### 2.GA4 Data API の有効化

GCP Consoleで [APIとサービス] → [ライブラリ] に移動します。
「Google Analytics Data API」を検索し、選択して [有効にする] をクリックします。

### 3.秘密鍵（JSONファイル）の作成とダウンロード

作成したサービスアカウントの詳細ページに戻ります。
[キー] タブをクリックします。
[キーを追加] → [新しいキーを作成] を選択します。
キーのタイプとして [JSON] を選択し、[作成] をクリックします。

JSONファイルが自動的にダウンロードされます。 これが秘密鍵です。ファイル名を your-service-account-key.json から変更した場合は、後の手順でそのファイル名を使用してください。

重要: このキーファイルは、後の手順で使用するため、スクリプトと同じフォルダ（utility/analytics_data/）に配置してください。

## ステップ 2: Google Analytics 4 (GA4) 側での権限付与

サービスアカウントに、GA4プロパティのデータへのアクセス権を与えます。<br>
Google Analyticsの管理画面にログインし、データを取得したいプロパティを開きます。<br>
画面左下の [管理] (歯車アイコン) をクリックします。<br>
プロパティ列にある [プロパティのアクセス管理] をクリックします。<br>
画面右上の青い [+] ボタンをクリックし、[ユーザーを追加] を選択します。<br>
メールアドレスを入力: ステップ1で作成したサービスアカウントのメールアドレス（例: ga4-reporter@your-project-id.iam.gserviceaccount.com）をコピー＆ペーストします。<br>
役割（ロール）を選択: [閲覧者] (Viewer) を選択します。<br>
[追加] ボタンをクリックします。

## ステップ 3: Python環境とスクリプトの設定

### 1.プロジェクト構造の確認

スクリプト（ga4_daily_report.py）とダウンロードしたJSONキーファイルが、同じフォルダ内に配置されていることを確認してください。

utility/<br>
└── analytics_data/<br>
    ├── venv/                       # 仮想環境フォルダ<br>
    ├── ga4_daily_report.py         # このPythonスクリプト<br>
    └── your-service-account-key.json # ダウンロードしたJSONキー (★ファイル名を合わせてください)


### 2.仮想環境の作成とライブラリのインストール

#### プロジェクトフォルダ (analytics_data) に移動
cd utility/analytics_data

#### 仮想環境を作成
python3 -m venv venv

#### 仮想環境をアクティブ化
source venv/bin/activate

#### 必要なライブラリをインストール
pip install google-analytics-data


### 3.スクリプトのパラメータ設定

ga4_daily_report.py ファイルを開き、以下の「設定パラメータ」をあなたの環境に合わせて修正します。

--- 設定パラメータ --- <br>
PROPERTY_ID = "509200578"  # <--- あなたのGA4プロパティID（数字のみ）<br>
START_DATE = "2025-11-01"  # <--- 取得開始日 (例: "2025-11-01") <br>
END_DATE = "2025-11-30"    # <--- 取得終了日 (例: "2025-11-30") <br>

### カスタムディメンションの場合、GA4管理画面で登録した名前の前に 'customEvent:' を付けます。
TARGET_DIMENSION_KEY = "customEvent:selected_language" 

### 行の表示順序設定 (ここにないディメンション値はCSVの末尾に追加されます)
ROW_ORDER = ["(not set)", "en", "ja", "ko", "zh-CN", "zh-TW"]

### --------------------
KEY_FILE_NAME = "your-service-account-key.json" # <--- ★ダウンロードしたJSONファイル名


## ステップ 4: スクリプトの実行

仮想環境がアクティブな状態で、スクリプトを実行します。<bt>
python ga4_daily_report.py

実行後、ga4_daily_report_pivot.csv というファイルが同じフォルダ内に生成されます。