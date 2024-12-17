import flet as fl
import json
import requests


def load_region_list():
    # Windows環境の場合は、エンコーディングを'shift-jis'に変更する必要があるかもしれません
    with open("課題１_fixed.json", "r", encoding="utf-8") as file:
        return json.load(file)


def parse_region_date(data):
    regions = {}
    try:
        for center_code, center_info in data["centers"].items():
            # 地域名を適切にデコード
            region_name = center_info["name"]
            if isinstance(region_name, bytes):
                region_name = region_name.decode('utf-8')
            
            regions[center_code] = {
                "name": region_name,
                "offices": {}
            }
            for office_code in center_info["children"]:
                if office_code in data["offices"]:
                    # 都道府県名を適切にデコード
                    office_name = data["offices"][office_code]["name"]
                    if isinstance(office_name, bytes):
                        office_name = office_name.decode('utf-8')
                    
                    regions[center_code]["offices"][office_code] = {
                        "name": office_name,
                        "class10s": {}
                    }
    except Exception as e:
        print(f"データの解析中にエラーが発生しました: {e}")
    return regions


def get_weather_data(region_code):
    """気象庁APIから天気データを取得する"""
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"天気データの取得中にエラーが発生しました: {e}")
        return None


def format_weather_info(weather_data):
    """天気情報を整形する"""
    weather_info_list = []
    try:
        # 天気予報データの取得
        time_series = weather_data[0]["timeSeries"]
        weather_areas = time_series[0]["areas"]
        
        # 降水確率データの取得
        precipitation_areas = time_series[1]["areas"] if len(time_series) > 1 else []

        # 各地域の天気情報を処理
        for area in weather_areas:
            area_name = area["area"]["name"]
            weather = area["weathers"][0]
            
            # 降水確率の取得
            precipitation_prob = "データなし"
            for p_area in precipitation_areas:
                if p_area["area"]["name"] == area_name:
                    probs = p_area.get("pops", ["--"])
                    precipitation_prob = f"{','.join(probs)}%"
                    break

            # 情報を整形
            info = f"{area_name}の天気: {weather}\n降水確率: {precipitation_prob}"
            weather_info_list.append(info)

    except Exception as e:
        weather_info_list.append(f"天気情報の解析に失敗しました: {str(e)}")

    return weather_info_list


def main(page: fl.Page):
    page.title = "天気予報アプリケーション"
    page.window.width = 1000
    page.window.height = 800
    page.padding = 20
    page.bgcolor = fl.colors.BLUE_GREY_50
    page.fonts = {
        "Noto Sans JP": "https://fonts.googleapis.com/css2?family=Noto+Sans+JP&display=swap"
    }
    page.theme = fl.Theme(font_family="Noto Sans JP")

    # データのロードと解析
    data = load_region_list()
    regions = parse_region_date(data)

    # 天気情報を表示するコンテナ
    weather_display = fl.Container(
        content=fl.Column(
            spacing=10,
            scroll=fl.ScrollMode.AUTO,
        ),
        padding=20,
        border=fl.border.all(2, fl.colors.BLUE_200),
        border_radius=10,
        bgcolor=fl.colors.WHITE,
        height=400,
        expand=True,
    )

    # UIコンポーネントの作成
    region_dropdown = fl.Dropdown(
        width=300,
        label="地域を選択",
        hint_text="地域を選んでください",
        border_color=fl.colors.BLUE_400,
        focused_border_color=fl.colors.BLUE_600,
        options=[
            fl.dropdown.Option(key=region_code, text=region_info["name"])
            for region_code, region_info in regions.items()
        ]
    )

    prefecture_dropdown = fl.Dropdown(
        width=300,
        label="都道府県を選択",
        hint_text="都道府県を選んでください",
        border_color=fl.colors.BLUE_400,
        focused_border_color=fl.colors.BLUE_600,
        options=[]
    )

    # ヘッダー部分
    header = fl.Container(
        content=fl.Row(
            controls=[
                fl.Icon(fl.icons.CLOUD, size=40, color=fl.colors.BLUE_400),
                fl.Text("天気予報アプリ", 
                       size=32, 
                       weight="bold",
                       color=fl.colors.BLUE_900),
            ],
            alignment=fl.MainAxisAlignment.CENTER,
        ),
        margin=fl.margin.only(bottom=20),
        padding=20,
        bgcolor=fl.colors.WHITE,
        border_radius=10,
    )

    # 選択部分のコンテナ
    selection_container = fl.Container(
        content=fl.Column(
            controls=[
                fl.Row(
                    controls=[
                        fl.Container(
                            content=region_dropdown,
                            padding=10,
                        ),
                        fl.Container(
                            content=prefecture_dropdown,
                            padding=10,
                        ),
                    ],
                    alignment=fl.MainAxisAlignment.CENTER,
                ),
            ],
        ),
        bgcolor=fl.colors.WHITE,
        padding=20,
        border_radius=10,
        margin=fl.margin.only(bottom=20),
    )

    # 天気情報表示部分のヘッダー
    weather_header = fl.Container(
        content=fl.Row(
            controls=[
                fl.Icon(fl.icons.SUNNY, color=fl.colors.ORANGE),
                fl.Text("天気情報", 
                       size=20, 
                       weight="bold",
                       color=fl.colors.BLUE_900),
            ],
        ),
        margin=fl.margin.only(bottom=10),
    )

    def on_region_change(e):
        selected_region_code = region_dropdown.value
        if selected_region_code:
            offices = regions[selected_region_code]["offices"]
            prefecture_dropdown.options = [
                fl.dropdown.Option(key=office_code, text=office_info["name"])
                for office_code, office_info in offices.items()
            ]
            prefecture_dropdown.value = None
            weather_display.content.controls.clear()
            page.update()

    def on_prefecture_change(e):
        selected_prefecture_code = prefecture_dropdown.value
        if selected_prefecture_code:
            weather_data = get_weather_data(selected_prefecture_code)
            weather_display.content.controls.clear()
            if weather_data:
                weather_texts = format_weather_info(weather_data)
                for text in weather_texts:
                    weather_display.content.controls.append(
                        fl.Container(
                            content=fl.Text(text, size=16),
                            bgcolor=fl.colors.BLUE_50,
                            padding=15,
                            border_radius=8,
                            margin=fl.margin.only(bottom=10),
                        )
                    )
            else:
                weather_display.content.controls.append(
                    fl.Container(
                        content=fl.Text(
                            "天気情報の取得に失敗しました。",
                            color=fl.colors.RED_400,
                            size=16,
                        ),
                        padding=15,
                    )
                )
            page.update()

    # イベントハンドラの設定
    region_dropdown.on_change = on_region_change
    prefecture_dropdown.on_change = on_prefecture_change

    # メインコンテンツ
    main_content = fl.Container(
        content=fl.Column(
            controls=[
                header,
                selection_container,
                weather_header,
                weather_display,
            ],
        ),
        margin=fl.margin.all(20),
    )

    page.add(main_content)
    page.update()


if __name__ == "__main__":
    fl.app(target=main)