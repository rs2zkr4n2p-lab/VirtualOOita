import os
import json
from datetime import datetime
from google import genai
from google.genai import types

def generate_markdown_from_json():
    # 1. spots.json の読み込み
    json_path = "data/spots.json"
    with open(json_path, "r", encoding="utf-8") as f:
        spots = json.load(f)
        
    # pending のスポットを1件探す
    target_spot = None
    target_index = -1
    for i, spot in enumerate(spots):
        if spot["status"] == "pending":
            target_spot = spot
            target_index = i
            break
            
    if not target_spot:
        print("処理待ちのスポットはねえよ（All completed!）")
        return

    print(f"【自動化拡張】{target_spot['name']} のMarkdownを生成中...")

    # 2. Gemini APIのクライアント初期化と生成（ここはさっきと同じ）
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません！")

    client = genai.Client(api_key=api_key)    

    system_instruction = (
        "あなたは『バーチャル大分』の案内人（大分のベテラン女将）です。"
        "大分県の観光・グルメ情報に精通しており、ユーザーには温かい大分弁で接してください。"
    )

    prompt = f"""
    以下の観光スポット情報を元に、Webサイトに掲載する魅力的な紹介文をMarkdown形式で生成してください。
    【スポット名】: {target_spot['name']}
    【カテゴリー】: {target_spot['category']}
    【タグ】: {', '.join(target_spot['tags'])}
    【一次情報URL】: {target_spot['source_url']}
    【概要】: {target_spot['description_summary']}
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )
    )

    # 3. Markdownファイルの書き出し
    os.makedirs("docs", exist_ok=True)
    file_name = f"docs/{target_spot['id'].replace('-', '_')}.md"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(response.text)
        
    print(f"🎉 成功！ {file_name} を書き出したよ！")

    # 🌟 ここからが肉付けポイント！台帳のステータスを更新
    spots[target_index]["status"] = "completed"
    spots[target_index]["last_updated"] = datetime.now().isoformat()

    # 更新されたインメモリのデータを spots.json に綺麗に上書き保存
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
        
    print(f"💾 台帳（{json_path}）のステータスを『completed』に更新したけんね！")

if __name__ == "__main__":
    generate_markdown_from_json()