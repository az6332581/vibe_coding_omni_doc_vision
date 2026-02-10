取代大量重複的人力肉眼檢查

📥 一、 輸入定義 (Input Definition)
影像文件 (Images/Video)：原始圖片或短影片
意圖描述 (User Query)：用戶隨圖附帶的文字（例：「這東西冒煙了」）。
設備環境 (Device Environment)：用戶使用的 App 版本、手機型號（對軟體客服至關重要）。
歷史記錄 (History Index)：該用戶過去 5 分鐘內傳過的照片（用於多輪對話追蹤）。
品質預檢 (Image Quality Assessment, IQA)

📤 二、 輸出定義 (Output Definition)
標記圖片 (Annotated Image)：在用戶原圖上畫圈、標箭頭（例：指向漏水的墊片）。
參考對照圖 (Reference Image)：從資料庫撈出的「標準正確狀態圖」。
標準作業程序 (SOP Steps)：精簡的 1, 2, 3 步驟指令。


📥 1. Input (輸入層)：
image_blob (原始圖檔)：系統的「眼睛」。
user_text (用戶提問)：搜尋的「意圖 (Intent)」。
metadata (環境參數)：後台的「輔助線」。包含用戶的設備型號、購買日期、GPS 定位等。

⚙️ 2. Process (處理層)：核心大腦
Preprocess (預處理)

路線一：影像處理 (Path 1: Image Processing)
1. 影像增強 (Image Enhancement)
2. 校正 (Perspective Correction)

路線二：文字提取 (Path 2: Text Extraction)
1. 光學字元辨識 (Optical Character Recognition, OCR)

Retrieve (檢索)
OCR 結果會與用戶提問 (user_text) 合併，形成更完整的搜尋條件。
1.多模態嵌入 (Multimodal Embedding)
2.混合檢索 (Hybrid Search)
3.Metadata 過濾

Re-rank (重排序)

Generate (生成)
🔥 難點：幻覺 (Hallucination)：AI 沒看清照片。

📤 3. Output (輸出層)：給用戶的答案
status (狀態碼)：success (成功)、need_more_info (需補拍)、human_required (轉接人工)。
identification (辨識結果)
annotation_url (標註圖)
steps_list (步驟清單)
next_action (後續動作)



💡 解決「幻覺 (Hallucination)」的具體方案
多視角驗證 (Multi-view Consistency)