import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const here = path.dirname(fileURLToPath(import.meta.url));
const bodyPath = path.resolve(here, "../教材_BUYMAロードマップ_Brain新版本文.md");
const previewDir = path.join(here, "プレビュー");
const checkedOn = "2026-07-13";

const COLORS = {
  navy: "#08233F",
  navy2: "#123B5D",
  gold: "#C89B3C",
  paleGold: "#F5EACB",
  white: "#FFFFFF",
  paper: "#FAFAF8",
  input: "#FFFDF4",
  formula: "#EAF3F8",
  line: "#D7DCE1",
  text: "#17202A",
  muted: "#5F6B76",
  red: "#FCE8E6",
  redText: "#A61B1B",
  green: "#E7F3EA",
  greenText: "#216E39",
  amber: "#FFF2CC",
  amberText: "#7A4D00",
};

const FONT_BODY = "Yu Gothic";
const FONT_TITLE = "Yu Mincho";

function colName(index) {
  let n = index + 1;
  let out = "";
  while (n > 0) {
    n -= 1;
    out = String.fromCharCode(65 + (n % 26)) + out;
    n = Math.floor(n / 26);
  }
  return out;
}

function styleTitle(sheet, lastCol, title, note) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: COLORS.navy,
    font: { name: FONT_TITLE, size: 18, bold: true, color: COLORS.white },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 32;

  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[note]];
  sheet.getRange(`A2:${lastCol}2`).format = {
    fill: COLORS.paleGold,
    font: { name: FONT_BODY, size: 10, color: COLORS.text },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(`A2:${lastCol}2`).format.rowHeight = 34;
}

function styleGrid(sheet, lastCol, lastRow, formulaCols = []) {
  const full = sheet.getRange(`A4:${lastCol}${lastRow}`);
  full.format = {
    font: { name: FONT_BODY, size: 9, color: COLORS.text },
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: COLORS.line },
  };
  sheet.getRange(`A4:${lastCol}4`).format = {
    fill: COLORS.navy2,
    font: { name: FONT_BODY, size: 9, bold: true, color: COLORS.white },
    wrapText: true,
    verticalAlignment: "center",
    horizontalAlignment: "center",
    borders: { preset: "all", style: "thin", color: COLORS.gold },
  };
  sheet.getRange(`A4:${lastCol}4`).format.rowHeight = 42;
  sheet.getRange(`A5:${lastCol}${lastRow}`).format.fill = COLORS.input;
  for (const col of formulaCols) {
    sheet.getRange(`${col}5:${col}${lastRow}`).format.fill = COLORS.formula;
  }
  sheet.freezePanes.freezeRows(4);
}

function setWidths(sheet, widths, lastRow) {
  for (let i = 0; i < widths.length; i += 1) {
    sheet.getRange(`${colName(i)}1:${colName(i)}${lastRow}`).format.columnWidth = widths[i];
  }
}

function addStatusFormatting(range) {
  range.conditionalFormats.add("containsText", {
    text: "STOP",
    format: { fill: COLORS.red, font: { color: COLORS.redText, bold: true } },
  });
  range.conditionalFormats.add("containsText", {
    text: "除外",
    format: { fill: COLORS.red, font: { color: COLORS.redText, bold: true } },
  });
  range.conditionalFormats.add("containsText", {
    text: "保留",
    format: { fill: COLORS.amber, font: { color: COLORS.amberText, bold: true } },
  });
  range.conditionalFormats.add("containsText", {
    text: "確認済み",
    format: { fill: COLORS.green, font: { color: COLORS.greenText, bold: true } },
  });
}

function addGuideSheet(workbook, title, filePurpose, sourceLinks, extraNotes = []) {
  const sheet = workbook.worksheets.add("使い方");
  sheet.showGridLines = false;
  sheet.getRange("A1:F1").merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1:F1").format = {
    fill: COLORS.navy,
    font: { name: FONT_TITLE, size: 18, bold: true, color: COLORS.white },
    verticalAlignment: "center",
  };
  sheet.getRange("A1:F1").format.rowHeight = 32;

  const rows = [
    ["目的", filePurpose],
    ["使い方 1", "黄色のセルに、確認できた事実だけを入力します。"],
    ["使い方 2", "水色のセルは計算欄です。式を上書きしないでください。"],
    ["使い方 3", "未確認、権利不明、販売元不明、検品経路なしの場合は実行せず止めます。"],
    ["記録しない", "パスワード、カード番号、本人確認書類、購入者の個人情報は入れません。証拠原本は権限を限定した保管先へ分離し、この表には参照先だけを記録します。"],
    ["確認日", checkedOn],
    ...extraNotes.map((note, index) => [`注意 ${index + 1}`, note]),
    ...sourceLinks.map((url, index) => [`公式確認先 ${index + 1}`, url]),
  ];
  sheet.getRange(`A3:B${rows.length + 2}`).values = rows;
  sheet.getRange(`A3:A${rows.length + 2}`).format = {
    fill: COLORS.paleGold,
    font: { name: FONT_BODY, bold: true, color: COLORS.text },
    verticalAlignment: "top",
    borders: { preset: "all", style: "thin", color: COLORS.line },
  };
  sheet.getRange(`B3:B${rows.length + 2}`).format = {
    fill: COLORS.paper,
    font: { name: FONT_BODY, color: COLORS.text },
    wrapText: true,
    verticalAlignment: "top",
    borders: { preset: "all", style: "thin", color: COLORS.line },
  };
  sheet.getRange(`A3:B${rows.length + 2}`).format.rowHeight = 32;
  sheet.getRange(`A1:A${rows.length + 2}`).format.columnWidth = 20;
  sheet.getRange(`B1:B${rows.length + 2}`).format.columnWidth = 78;
  return sheet;
}

function addSettingsSheet(workbook, title, rows) {
  const sheet = workbook.worksheets.add("設定");
  sheet.showGridLines = false;
  sheet.getRange("A1:D1").merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1:D1").format = {
    fill: COLORS.navy,
    font: { name: FONT_TITLE, size: 16, bold: true, color: COLORS.white },
  };
  sheet.getRange(`A3:C${rows.length + 2}`).values = rows;
  sheet.getRange(`A3:A${rows.length + 2}`).format = {
    fill: COLORS.paleGold,
    font: { name: FONT_BODY, bold: true, color: COLORS.text },
    borders: { preset: "all", style: "thin", color: COLORS.line },
  };
  sheet.getRange(`B3:B${rows.length + 2}`).format = {
    fill: COLORS.input,
    font: { name: FONT_BODY, color: COLORS.text },
    borders: { preset: "all", style: "thin", color: COLORS.line },
  };
  sheet.getRange(`C3:C${rows.length + 2}`).format = {
    fill: COLORS.paper,
    font: { name: FONT_BODY, color: COLORS.muted },
    wrapText: true,
    borders: { preset: "all", style: "thin", color: COLORS.line },
  };
  sheet.getRange(`A1:A${rows.length + 2}`).format.columnWidth = 24;
  sheet.getRange(`B1:B${rows.length + 2}`).format.columnWidth = 24;
  sheet.getRange(`C1:C${rows.length + 2}`).format.columnWidth = 72;
  return sheet;
}

async function saveAndVerify(workbook, fileName, previews, checks) {
  await fs.mkdir(previewDir, { recursive: true });
  const formulaErrors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: `${fileName} formula error scan`,
    maxChars: 6000,
  });
  const hasFormulaErrors = formulaErrors.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .some((entry) => entry.kind !== "notice");
  if (hasFormulaErrors) {
    throw new Error(`${fileName}: formula error detected\n${formulaErrors.ndjson}`);
  }

  for (const check of checks) {
    const inspected = await workbook.inspect({
      kind: "table",
      sheetId: check.sheet,
      range: check.range,
      include: "values,formulas",
      tableMaxRows: 12,
      tableMaxCols: 30,
      maxChars: 6000,
    });
    console.log(`CHECK ${fileName} ${check.sheet}!${check.range}`);
    console.log(inspected.ndjson);
  }

  for (const preview of previews) {
    const image = await workbook.render({
      sheetName: preview.sheet,
      range: preview.range,
      scale: 1,
      format: "png",
    });
    const previewName = `${fileName.replace(/\.xlsx$/, "")}_${preview.sheet}.png`;
    await fs.writeFile(path.join(previewDir, previewName), new Uint8Array(await image.arrayBuffer()));
  }

  const outputPath = path.join(here, fileName);
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(outputPath);

  const reloaded = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
  const reloadedErrors = await reloaded.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: `${fileName} post-export formula error scan`,
    maxChars: 6000,
  });
  const hasReloadedErrors = reloadedErrors.ndjson
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .some((entry) => entry.kind !== "notice");
  if (hasReloadedErrors) {
    throw new Error(`${fileName}: post-export formula error detected\n${reloadedErrors.ndjson}`);
  }
  console.log(`EXPORTED ${outputPath}`);
}

async function buildProfitWorkbook() {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("利益計算");
  const settings = addSettingsSheet(workbook, "利益計算の設定", [
    ["項目", "入力値", "説明"],
    ["BUYMA成約手数料率", null, "自分のアカウントと注文条件に適用される現行率をBUYMA公式画面で確認し、割合で入力します。例: 7.5%なら7.5%。"],
    ["確認日", null, "手数料率を確認した日"],
    ["根拠URL・画面メモ", "https://qa.buyma.com/shopper/", "ログイン後の現行表示も確認してください。"],
  ]);
  addGuideSheet(
    workbook,
    "BUYMA 利益計算表 購入者版",
    "商品ごとの総コスト、利益、利益率を、現行の手数料率と実額から計算します。",
    [
      "https://qa.buyma.com/shopper/sell/1501.html",
      "https://qa.buyma.com/buy/pay/3104.html",
      "https://www.customs.go.jp/",
    ],
    ["空欄を0円と決めつけず、発生可能性がある費用は確認してから判断してください。"],
  );

  const headers = [
    "管理番号", "商品名", "販売価格(JPY)", "商品代金(現地通貨)", "為替レート(JPY)", "商品代金円換算", "現地送料(JPY)", "国際送料(JPY)", "関税等(JPY)", "決済・送金手数料(JPY)", "成約手数料率", "成約手数料(JPY)", "外注費(JPY)", "その他経費(JPY)", "総コスト(JPY)", "利益(JPY)", "利益率", "判定", "確認日", "根拠URL・メモ",
  ];
  const lastRow = 104;
  sheet.getRange("A4:T4").values = [headers];
  styleTitle(sheet, "T", "BUYMA 利益計算表 購入者版", "販売価格・仕入・送料・税・手数料・外注費を商品単位で入力。水色は自動計算です。");
  styleGrid(sheet, "T", lastRow, ["F", "K", "L", "O", "P", "Q", "R"]);
  setWidths(sheet, [13, 24, 14, 17, 14, 16, 14, 14, 13, 18, 13, 16, 13, 14, 16, 14, 12, 12, 13, 36], lastRow);

  sheet.getRange("F5").formulas = [["=IF(OR(D5=\"\",E5=\"\"),\"\",D5*E5)"]];
  sheet.getRange("F5:F104").fillDown();
  sheet.getRange("K5").formulas = [["=IF(OR(C5=\"\",'設定'!$B$4=\"\"),\"\",'設定'!$B$4)"]];
  sheet.getRange("K5:K104").fillDown();
  sheet.getRange("L5").formulas = [["=IF(OR(C5=\"\",K5=\"\"),\"\",C5*K5)"]];
  sheet.getRange("L5:L104").fillDown();
  sheet.getRange("O5").formulas = [["=IF(OR(C5=\"\",F5=\"\",L5=\"\"),\"\",SUM(F5:J5,L5:N5))"]];
  sheet.getRange("O5:O104").fillDown();
  sheet.getRange("P5").formulas = [["=IF(O5=\"\",\"\",C5-O5)"]];
  sheet.getRange("P5:P104").fillDown();
  sheet.getRange("Q5").formulas = [["=IF(OR(C5=\"\",C5=0,P5=\"\"),\"\",P5/C5)"]];
  sheet.getRange("Q5:Q104").fillDown();
  sheet.getRange("R5").formulas = [["=IF(A5=\"\",\"\",IF(OR(F5=\"\",K5=\"\"),\"STOP: 未入力\",IF(P5<=0,\"STOP: 利益なし\",\"要確認\")))"]];
  sheet.getRange("R5:R104").fillDown();

  sheet.getRange("C5:P104").format.numberFormat = "#,##0";
  sheet.getRange("K5:K104").format.numberFormat = "0.00%";
  sheet.getRange("Q5:Q104").format.numberFormat = "0.0%";
  sheet.getRange("S5:S104").format.numberFormat = "yyyy-mm-dd";
  addStatusFormatting(sheet.getRange("R5:R104"));

  settings.getRange("B4").values = [[0.075]];
  sheet.getRange("A104:E104").values = [["QA-001", "テスト", 100000, 500, 150]];
  sheet.getRange("G104:J104").values = [[1000, 2000, 3000, 500]];
  sheet.getRange("M104:N104").values = [[1000, 0]];
  const testProfit = sheet.getRange("P104").values[0][0];
  const testMargin = sheet.getRange("Q104").values[0][0];
  if (Math.abs(Number(testProfit) - 10000) > 0.01 || Math.abs(Number(testMargin) - 0.1) > 0.0001) {
    throw new Error(`利益計算テスト失敗: profit=${testProfit}, margin=${testMargin}`);
  }
  sheet.getRange("A104:E104").clear({ applyTo: "contents" });
  sheet.getRange("G104:J104").clear({ applyTo: "contents" });
  sheet.getRange("M104:N104").clear({ applyTo: "contents" });
  settings.getRange("B4").clear({ applyTo: "contents" });

  await saveAndVerify(
    workbook,
    "BUYMA_利益計算表_購入者版.xlsx",
    [
      { sheet: "利益計算", range: "A1:T12" },
      { sheet: "設定", range: "A1:C7" },
      { sheet: "使い方", range: "A1:B12" },
    ],
    [
      { sheet: "利益計算", range: "A4:T8" },
      { sheet: "設定", range: "A3:C7" },
    ],
  );
}

async function buildListingWorkbook() {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("出品管理");
  const settings = addSettingsSheet(workbook, "出品管理の設定", [
    ["項目", "入力値", "説明"],
    ["BUYMA成約手数料率", null, "現行率を自分の画面で確認して入力します。"],
    ["確認日", null, "手数料率を確認した日"],
    ["公式確認先", "https://qa.buyma.com/shopper/", "禁止買付先、画像権利、出品項目も公開前に再確認します。"],
  ]);
  addGuideSheet(
    workbook,
    "BUYMA 出品管理表 購入者版",
    "候補登録から公開前承認、利益確認、更新日までを1商品1行で管理します。",
    [
      "https://qa.buyma.com/shopper/prohibited-item/4007.html",
      "https://qa.buyma.com/shopper/prohibited-item/15733.html",
      "https://qa.buyma.com/shopper/sell/",
    ],
    ["権利不明の画像、販売元不明、利益未計算、確認者未承認の行は公開しません。"],
  );

  const headers = [
    "管理番号", "進行状況", "ブランド", "商品名", "型番", "色・サイズ", "公式商品URL", "買付先URL", "実販売元", "在庫・価格確認日時", "画像利用根拠", "証拠保管先", "商品代金(JPY)", "国内送料", "国際送料", "関税等", "決済・その他", "外注費", "成約手数料率", "販売価格", "成約手数料", "総コスト", "利益", "利益率", "作業担当", "確認者", "公開前判定", "公開日", "更新日", "備考",
  ];
  const lastRow = 104;
  sheet.getRange("A4:AD4").values = [headers];
  styleTitle(sheet, "AD", "BUYMA 出品管理表 購入者版", "候補・権利・買付先・利益・確認者を1行で追跡。水色は自動計算です。");
  styleGrid(sheet, "AD", lastRow, ["S", "U", "V", "W", "X", "AA"]);
  setWidths(sheet, [13, 14, 18, 24, 14, 16, 32, 32, 20, 20, 22, 25, 14, 12, 12, 12, 14, 12, 13, 14, 14, 15, 14, 12, 14, 14, 16, 13, 13, 30], lastRow);

  sheet.getRange("S5").formulas = [["=IF(OR(A5=\"\",'設定'!$B$4=\"\"),\"\",'設定'!$B$4)"]];
  sheet.getRange("S5:S104").fillDown();
  sheet.getRange("U5").formulas = [["=IF(OR(T5=\"\",S5=\"\"),\"\",T5*S5)"]];
  sheet.getRange("U5:U104").fillDown();
  sheet.getRange("V5").formulas = [["=IF(OR(A5=\"\",U5=\"\"),\"\",SUM(M5:R5,U5))"]];
  sheet.getRange("V5:V104").fillDown();
  sheet.getRange("W5").formulas = [["=IF(OR(T5=\"\",V5=\"\"),\"\",T5-V5)"]];
  sheet.getRange("W5:W104").fillDown();
  sheet.getRange("X5").formulas = [["=IF(OR(T5=\"\",T5=0,W5=\"\"),\"\",W5/T5)"]];
  sheet.getRange("X5:X104").fillDown();
  sheet.getRange("AA5").formulas = [["=IF(A5=\"\",\"\",IF(OR(H5=\"\",I5=\"\",J5=\"\",K5=\"\",S5=\"\",T5=\"\",Z5=\"\"),\"STOP: 確認不足\",IF(W5<=0,\"STOP: 利益なし\",\"確認済み\")))"]];
  sheet.getRange("AA5:AA104").fillDown();

  sheet.getRange("B5:B104").dataValidation = { rule: { type: "list", values: ["候補", "確認中", "下書き", "承認待ち", "公開", "停止"] } };
  sheet.getRange("M5:W104").format.numberFormat = "#,##0";
  sheet.getRange("S5:S104").format.numberFormat = "0.00%";
  sheet.getRange("X5:X104").format.numberFormat = "0.0%";
  sheet.getRange("J5:J104").format.numberFormat = "yyyy-mm-dd hh:mm";
  sheet.getRange("AB5:AC104").format.numberFormat = "yyyy-mm-dd";
  addStatusFormatting(sheet.getRange("AA5:AA104"));

  const customs = workbook.worksheets.add("関税・分類確認");
  const customsHeaders = ["管理番号", "商品分類", "素材", "原産国", "発送国", "想定税率", "関税等見込額", "確認日", "根拠URL", "確認者", "備考"];
  customs.getRange("A4:K4").values = [customsHeaders];
  styleTitle(customs, "K", "関税・分類確認", "一律税率を使わず、商品分類・素材・原産国・発送国と公式根拠を記録します。");
  styleGrid(customs, "K", 104, []);
  setWidths(customs, [13, 20, 18, 14, 14, 13, 16, 13, 40, 14, 28], 104);
  customs.getRange("F5:G104").format.numberFormat = "0.00%";
  customs.getRange("H5:H104").format.numberFormat = "yyyy-mm-dd";

  settings.getRange("B4").values = [[0.075]];
  sheet.getRange("A104:L104").values = [["QA-001", "承認待ち", "TEST", "テスト", "T-1", "黒/M", "https://example.com/official", "https://example.com/shop", "Test Seller", new Date("2026-07-13T00:00:00Z"), "利用許可確認", "restricted://evidence"]];
  sheet.getRange("M104:R104").values = [[70000, 1000, 2000, 3000, 500, 1000]];
  sheet.getRange("T104").values = [[100000]];
  sheet.getRange("Z104").values = [["確認者"]];
  const testProfit = Number(sheet.getRange("W104").values[0][0]);
  if (Math.abs(testProfit - 15000) > 0.01) {
    throw new Error(`出品管理テスト失敗: profit=${testProfit}`);
  }
  sheet.getRange("A104:L104").clear({ applyTo: "contents" });
  sheet.getRange("M104:R104").clear({ applyTo: "contents" });
  sheet.getRange("T104").clear({ applyTo: "contents" });
  sheet.getRange("Z104").clear({ applyTo: "contents" });
  settings.getRange("B4").clear({ applyTo: "contents" });

  await saveAndVerify(
    workbook,
    "BUYMA_出品管理表_購入者版.xlsx",
    [
      { sheet: "出品管理", range: "A1:AD11" },
      { sheet: "関税・分類確認", range: "A1:K11" },
      { sheet: "設定", range: "A1:C7" },
      { sheet: "使い方", range: "A1:B12" },
    ],
    [
      { sheet: "出品管理", range: "A4:AD7" },
      { sheet: "関税・分類確認", range: "A4:K7" },
    ],
  );
}

async function buildDomesticWorkbook() {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("国内買付管理");
  addGuideSheet(
    workbook,
    "BUYMA 国内買付管理表 購入者版",
    "依頼、店舗確認、買付、受取、検品、発送、精算を1つの管理番号でつなぎます。",
    [
      "https://qa.buyma.com/shopper/prohibited-item/4007.html",
      "https://qa.buyma.com/shopper/order-to-delivery/4201.html",
      "https://qa.buyma.com/shopper/order-to-delivery/4202.html",
    ],
    ["クラウドソーシングサービスの禁止業務に該当する代理購入・受取等は掲載しません。募集先ごとの現行規約を確認してください。"],
  );

  const headers = [
    "管理番号", "進行状況", "依頼日", "ブランド", "商品名", "商品URL", "型番", "色", "サイズ", "店舗・支店", "在庫確認日時", "買付担当", "買付日", "商品代金", "交通費", "国内送料", "立替経費", "パートナー報酬", "その他", "総支出", "前払額", "精算差額", "受取日", "検品結果", "検品証拠保管先", "発送方法", "追跡番号", "発送日", "発送控え保管先", "精算日", "備考",
  ];
  const lastRow = 104;
  sheet.getRange("A4:AE4").values = [headers];
  styleTitle(sheet, "AE", "BUYMA 国内買付管理表 購入者版", "1取引1行。総支出と精算差額は自動計算です。");
  styleGrid(sheet, "AE", lastRow, ["T", "V"]);
  setWidths(sheet, [13, 14, 13, 18, 22, 32, 14, 12, 12, 20, 18, 14, 13, 13, 12, 12, 12, 14, 12, 15, 13, 14, 13, 16, 26, 18, 18, 13, 24, 13, 30], lastRow);
  sheet.getRange("T5").formulas = [["=IF(A5=\"\",\"\",SUM(N5:S5))"]];
  sheet.getRange("T5:T104").fillDown();
  sheet.getRange("V5").formulas = [["=IF(A5=\"\",\"\",T5-U5)"]];
  sheet.getRange("V5:V104").fillDown();
  sheet.getRange("B5:B104").dataValidation = { rule: { type: "list", values: ["依頼", "在庫確認", "買付済み", "受取済み", "検品待ち", "発送済み", "完了", "停止"] } };
  sheet.getRange("X5:X104").dataValidation = { rule: { type: "list", values: ["未確認", "合格", "不一致", "傷・破損", "停止"] } };
  sheet.getRange("C5:C104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("K5:K104").format.numberFormat = "yyyy-mm-dd hh:mm";
  sheet.getRange("M5:M104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("N5:V104").format.numberFormat = "#,##0";
  sheet.getRange("W5:W104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("AB5:AD104").format.numberFormat = "yyyy-mm-dd";
  addStatusFormatting(sheet.getRange("B5:B104"));
  addStatusFormatting(sheet.getRange("X5:X104"));

  const expenses = workbook.worksheets.add("経費・精算明細");
  const expenseHeaders = ["管理番号", "発生日", "区分", "内容", "金額", "支払者", "証憑保管先", "前払・立替", "精算日", "入力者", "備考"];
  expenses.getRange("A4:K4").values = [expenseHeaders];
  styleTitle(expenses, "K", "経費・精算明細", "本表の合計と国内買付管理の費用を二重計上しないでください。");
  styleGrid(expenses, "K", 204, []);
  setWidths(expenses, [13, 13, 16, 24, 14, 14, 28, 16, 13, 14, 26], 204);
  expenses.getRange("C5:C204").dataValidation = { rule: { type: "list", values: ["商品代金", "交通費", "送料", "梱包", "報酬", "その他"] } };
  expenses.getRange("B5:B204").format.numberFormat = "yyyy-mm-dd";
  expenses.getRange("E5:E204").format.numberFormat = "#,##0";
  expenses.getRange("I5:I204").format.numberFormat = "yyyy-mm-dd";

  sheet.getRange("A104:S104").values = [["QA-001", "買付済み", new Date("2026-07-13"), "TEST", "テスト", "https://example.com", "T-1", "黒", "M", "店舗", new Date("2026-07-13"), "担当", new Date("2026-07-13"), 50000, 1000, 800, 200, 1500, 500]];
  sheet.getRange("U104").values = [[40000]];
  if (Number(sheet.getRange("T104").values[0][0]) !== 54000 || Number(sheet.getRange("V104").values[0][0]) !== 14000) {
    throw new Error("国内買付の総支出・精算差額テスト失敗");
  }
  sheet.getRange("A104:S104").clear({ applyTo: "contents" });
  sheet.getRange("U104").clear({ applyTo: "contents" });

  await saveAndVerify(
    workbook,
    "BUYMA_国内買付管理表_購入者版.xlsx",
    [
      { sheet: "国内買付管理", range: "A1:AE11" },
      { sheet: "経費・精算明細", range: "A1:K11" },
      { sheet: "使い方", range: "A1:B13" },
    ],
    [
      { sheet: "国内買付管理", range: "A4:AE7" },
      { sheet: "経費・精算明細", range: "A4:K7" },
    ],
  );
}

async function buildOverseasWorkbook() {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("海外買付管理");
  addGuideSheet(
    workbook,
    "BUYMA 海外買付管理表 購入者版",
    "海外パートナーへの依頼、買付、受取、検品、国際発送、精算を記録します。",
    [
      "https://qa.buyma.com/shopper/prohibited-item/4007.html",
      "https://qa.buyma.com/shopper/order-to-delivery/4201.html",
      "https://qa.buyma.com/shopper/order-to-delivery/4202.html",
      "https://www.ppc.go.jp/",
    ],
    ["購入者情報を外国にいるパートナーへ渡す場合は、必要最小限・提供条件・保管期限・削除手順を事前に確認します。"],
  );

  const headers = [
    "管理番号", "進行状況", "依頼日", "国・地域", "パートナー", "ブランド", "商品名", "商品URL", "型番", "色・サイズ", "注文番号", "買付日", "現地通貨", "商品価格(現地通貨)", "為替レート", "商品価格円換算", "現地送料(JPY)", "国際送料(JPY)", "関税等(JPY)", "送金手数料(JPY)", "パートナー報酬(JPY)", "その他(JPY)", "総支出(JPY)", "前払額(JPY)", "精算差額(JPY)", "受取日", "検品結果", "検品証拠保管先", "発送方法", "追跡番号", "発送日", "発送控え保管先", "外国提供確認", "削除確認日", "備考",
  ];
  const lastRow = 104;
  sheet.getRange("A4:AI4").values = [headers];
  styleTitle(sheet, "AI", "BUYMA 海外買付管理表 購入者版", "現地通貨と為替を分け、円換算・総支出・精算差額を自動計算します。");
  styleGrid(sheet, "AI", lastRow, ["P", "W", "Y"]);
  setWidths(sheet, [13, 14, 13, 14, 16, 18, 22, 32, 14, 16, 16, 13, 11, 17, 13, 17, 14, 14, 13, 15, 16, 13, 16, 14, 15, 13, 16, 26, 18, 18, 13, 24, 16, 13, 30], lastRow);
  sheet.getRange("P5").formulas = [["=IF(OR(N5=\"\",O5=\"\"),\"\",N5*O5)"]];
  sheet.getRange("P5:P104").fillDown();
  sheet.getRange("W5").formulas = [["=IF(OR(A5=\"\",P5=\"\"),\"\",SUM(P5:V5))"]];
  sheet.getRange("W5:W104").fillDown();
  sheet.getRange("Y5").formulas = [["=IF(A5=\"\",\"\",W5-X5)"]];
  sheet.getRange("Y5:Y104").fillDown();
  sheet.getRange("B5:B104").dataValidation = { rule: { type: "list", values: ["依頼", "注文済み", "受取済み", "検品待ち", "発送済み", "完了", "停止"] } };
  sheet.getRange("AA5:AA104").dataValidation = { rule: { type: "list", values: ["未確認", "合格", "不一致", "傷・破損", "停止"] } };
  sheet.getRange("AG5:AG104").dataValidation = { rule: { type: "list", values: ["不要", "確認済み", "要確認", "提供停止"] } };
  sheet.getRange("C5:C104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("L5:L104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("N5:Y104").format.numberFormat = "#,##0.00";
  sheet.getRange("O5:O104").format.numberFormat = "0.0000";
  sheet.getRange("Z5:Z104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("AE5:AE104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("AH5:AH104").format.numberFormat = "yyyy-mm-dd";
  addStatusFormatting(sheet.getRange("B5:B104"));
  addStatusFormatting(sheet.getRange("AA5:AA104"));
  addStatusFormatting(sheet.getRange("AG5:AG104"));

  const expenses = workbook.worksheets.add("経費・送金明細");
  const expenseHeaders = ["管理番号", "発生日", "区分", "通貨", "現地金額", "為替レート", "円換算", "支払者", "証憑保管先", "送金日", "精算日", "入力者", "備考"];
  expenses.getRange("A4:M4").values = [expenseHeaders];
  styleTitle(expenses, "M", "経費・送金明細", "本表の合計を海外買付管理へ転記する場合は、同じ費用を二重計上しないでください。");
  styleGrid(expenses, "M", 204, ["G"]);
  setWidths(expenses, [13, 13, 18, 11, 14, 13, 14, 14, 28, 13, 13, 14, 28], 204);
  expenses.getRange("G5").formulas = [["=IF(OR(E5=\"\",F5=\"\"),\"\",E5*F5)"]];
  expenses.getRange("G5:G204").fillDown();
  expenses.getRange("C5:C204").dataValidation = { rule: { type: "list", values: ["商品代金", "現地送料", "国際送料", "関税等", "送金手数料", "報酬", "その他"] } };
  expenses.getRange("B5:B204").format.numberFormat = "yyyy-mm-dd";
  expenses.getRange("E5:G204").format.numberFormat = "#,##0.00";
  expenses.getRange("J5:K204").format.numberFormat = "yyyy-mm-dd";

  sheet.getRange("A104:O104").values = [["QA-001", "注文済み", new Date("2026-07-13"), "US", "担当", "TEST", "テスト", "https://example.com", "T-1", "黒/M", "ORDER-1", new Date("2026-07-13"), "USD", 500, 150]];
  sheet.getRange("Q104:V104").values = [[1000, 2000, 3000, 500, 1000, 500]];
  sheet.getRange("X104").values = [[70000]];
  if (Number(sheet.getRange("P104").values[0][0]) !== 75000 || Number(sheet.getRange("W104").values[0][0]) !== 83000 || Number(sheet.getRange("Y104").values[0][0]) !== 13000) {
    throw new Error("海外買付の円換算・総支出・精算差額テスト失敗");
  }
  sheet.getRange("A104:O104").clear({ applyTo: "contents" });
  sheet.getRange("Q104:V104").clear({ applyTo: "contents" });
  sheet.getRange("X104").clear({ applyTo: "contents" });

  await saveAndVerify(
    workbook,
    "BUYMA_海外買付管理表_購入者版.xlsx",
    [
      { sheet: "海外買付管理", range: "A1:AI11" },
      { sheet: "経費・送金明細", range: "A1:M11" },
      { sheet: "使い方", range: "A1:B14" },
    ],
    [
      { sheet: "海外買付管理", range: "A4:AI7" },
      { sheet: "経費・送金明細", range: "A4:M7" },
    ],
  );
}

async function buildDirectWorkbook() {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("直営店確認台帳");
  addGuideSheet(
    workbook,
    "BUYMA 直営店連携確認台帳 購入者版",
    "直営店・正規店との連携条件を、問い合わせ回答と検品経路まで含めて記録します。",
    [
      "https://qa.buyma.com/shopper/prohibited-item/4007.html",
      "https://qa.buyma.com/shopper/order-to-delivery/4201.html",
      "https://qa.buyma.com/shopper/prohibited-item/15733.html",
    ],
    ["旧候補267件は、現行営業・公式連絡先・条件を確認できていないため収録していません。確認済みの候補だけを追加してください。"],
  );

  const headers = [
    "管理番号", "ブランド", "店舗名", "国・地域", "公式URL", "公式問い合わせ先", "確認日", "運営主体", "実販売元", "在庫確認方法", "日本へ発送", "検品者へ発送", "現物検品経路", "写真・動画対応", "画像利用許可", "許可範囲・期限", "購入証明・インボイス", "税・VAT", "決済方法・通貨", "配送・追跡・補償", "返品・返金条件", "回答原文保管先", "最終判断", "判断理由", "次回確認日", "確認者", "変更履歴・備考",
  ];
  const lastRow = 104;
  sheet.getRange("A4:AA4").values = [headers];
  styleTitle(sheet, "AA", "BUYMA 直営店連携確認台帳 購入者版", "直送可否だけで判断せず、現物検品・返品・画像許可・購入証明まで記録します。");
  styleGrid(sheet, "AA", lastRow, []);
  setWidths(sheet, [13, 18, 20, 14, 32, 26, 13, 20, 20, 20, 13, 14, 22, 18, 18, 22, 22, 18, 22, 24, 26, 28, 14, 26, 13, 14, 34], lastRow);
  sheet.getRange("K5:L104").dataValidation = { rule: { type: "list", values: ["未確認", "可", "不可", "条件あり"] } };
  sheet.getRange("W5:W104").dataValidation = { rule: { type: "list", values: ["未確認", "候補", "保留", "除外"] } };
  sheet.getRange("G5:G104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("Y5:Y104").format.numberFormat = "yyyy-mm-dd";
  addStatusFormatting(sheet.getRange("W5:W104"));

  const inquiry = workbook.worksheets.add("問い合わせ記録");
  const inquiryHeaders = ["管理番号", "送信日", "手段", "宛先", "質問項目", "回答日", "回答要約", "回答原文保管先", "再確認事項", "担当者", "備考"];
  inquiry.getRange("A4:K4").values = [inquiryHeaders];
  styleTitle(inquiry, "K", "直営店 問い合わせ記録", "重要条件は担当者名・回答日・原文を残し、推測で補完しません。");
  styleGrid(inquiry, "K", 204, []);
  setWidths(inquiry, [13, 13, 14, 22, 34, 13, 34, 28, 28, 14, 26], 204);
  inquiry.getRange("B5:B204").format.numberFormat = "yyyy-mm-dd";
  inquiry.getRange("F5:F204").format.numberFormat = "yyyy-mm-dd";

  await saveAndVerify(
    workbook,
    "BUYMA_直営店連携確認台帳_購入者版.xlsx",
    [
      { sheet: "直営店確認台帳", range: "A1:AA11" },
      { sheet: "問い合わせ記録", range: "A1:K11" },
      { sheet: "使い方", range: "A1:B13" },
    ],
    [
      { sheet: "直営店確認台帳", range: "A4:AA7" },
      { sheet: "問い合わせ記録", range: "A4:K7" },
    ],
  );
}

async function buildVipWorkbook() {
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("VIP交渉管理");
  addGuideSheet(
    workbook,
    "BUYMA VIP交渉管理表 購入者版",
    "オンラインVIP制度の有無、適用条件、注文ごとの利益、継続可否を証拠付きで管理します。",
    [
      "https://qa.buyma.com/shopper/prohibited-item/4007.html",
      "https://qa.buyma.com/shopper/sell/1501.html",
    ],
    ["旧サンプルのコード・20%は実在条件として引き継いでいません。割引率や適用条件は現在の回答を入力してください。"],
  );

  const headers = [
    "管理番号", "サイト・店舗", "公式URL", "国・地域", "公式窓口", "初回確認日", "制度の有無", "対象条件", "割引方式", "割引率", "最低購入額", "対象外ブランド・商品", "コード・条件の保管先", "有効期限", "送料条件", "税・関税", "返品条件", "併用条件", "回答原文保管先", "試算管理番号", "テスト注文結果", "最終判断", "次回連絡日", "担当者", "備考",
  ];
  const lastRow = 104;
  sheet.getRange("A4:Y4").values = [headers];
  styleTitle(sheet, "Y", "BUYMA VIP交渉管理表 購入者版", "制度があるだけで採用せず、対象外条件・期限・返品・注文ごとの利益を確認します。");
  styleGrid(sheet, "Y", lastRow, []);
  setWidths(sheet, [13, 22, 32, 14, 24, 13, 15, 24, 16, 12, 15, 26, 26, 13, 22, 18, 24, 22, 28, 16, 22, 14, 13, 14, 30], lastRow);
  sheet.getRange("G5:G104").dataValidation = { rule: { type: "list", values: ["未確認", "あり", "なし", "招待制", "条件あり"] } };
  sheet.getRange("V5:V104").dataValidation = { rule: { type: "list", values: ["未確認", "継続候補", "保留", "除外"] } };
  sheet.getRange("F5:F104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("J5:J104").format.numberFormat = "0.00%";
  sheet.getRange("K5:K104").format.numberFormat = "#,##0.00";
  sheet.getRange("N5:N104").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("W5:W104").format.numberFormat = "yyyy-mm-dd";
  addStatusFormatting(sheet.getRange("V5:V104"));

  const history = workbook.worksheets.add("交渉履歴");
  const historyHeaders = ["管理番号", "連絡日", "手段", "宛先", "依頼内容", "回答日", "回答要約", "条件変更", "原文保管先", "担当者", "次回対応", "備考"];
  history.getRange("A4:L4").values = [historyHeaders];
  styleTitle(history, "L", "VIP 交渉履歴", "条件変更を上書きせず、連絡日と回答原文を残します。");
  styleGrid(history, "L", 204, []);
  setWidths(history, [13, 13, 14, 22, 34, 13, 34, 24, 28, 14, 24, 26], 204);
  history.getRange("B5:B204").format.numberFormat = "yyyy-mm-dd";
  history.getRange("F5:F204").format.numberFormat = "yyyy-mm-dd";

  await saveAndVerify(
    workbook,
    "BUYMA_VIP交渉管理表_購入者版.xlsx",
    [
      { sheet: "VIP交渉管理", range: "A1:Y11" },
      { sheet: "交渉履歴", range: "A1:L11" },
      { sheet: "使い方", range: "A1:B13" },
    ],
    [
      { sheet: "VIP交渉管理", range: "A4:Y7" },
      { sheet: "交渉履歴", range: "A4:L7" },
    ],
  );
}

function plainMarkdown(text) {
  return text
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, "$1")
    .replace(/\*\*/g, "")
    .trim();
}

function firstUrl(text) {
  const match = text.match(/\[[^\]]+\]\((https?:\/\/[^)]+)\)/);
  return match ? match[1] : "";
}

function normalizeShopStatus(raw) {
  if (raw.includes("国内EC")) return "除外";
  if (raw.includes("要再確認")) return "要再確認";
  if (raw.includes("営業表示あり")) return "営業表示あり";
  if (raw.includes("URL") || raw.includes("運営変更") || raw.includes("単独EC終了") || raw.includes("事業変更")) return "URL・名称・運営変更";
  if (raw.includes("閉鎖") || raw.includes("EC終了")) return "閉鎖";
  return "要再確認";
}

async function parseShopRows() {
  const body = await fs.readFile(bodyPath, "utf8");
  const section = body.split("### 6-2 原教材68件の現況監査表")[1]?.split("### 6-3 購入者版ショップ管理表の列")[0] ?? "";
  const rows = [];
  for (const line of section.split(/\r?\n/)) {
    const match = line.match(/^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|$/);
    if (!match) continue;
    const no = Number(match[1]);
    if (no < 1 || no > 68) continue;
    const rawStatus = plainMarkdown(match[4]);
    rows.push({
      no,
      oldName: plainMarkdown(match[2]),
      oldCountry: plainMarkdown(match[3]),
      status: normalizeShopStatus(rawStatus),
      rawStatus,
      url: firstUrl(match[5]),
      note: plainMarkdown(match[5]),
    });
  }
  rows.sort((a, b) => a.no - b.no);
  if (rows.length !== 68 || rows.some((row, index) => row.no !== index + 1)) {
    throw new Error(`ショップ監査表の抽出失敗: ${rows.length}件`);
  }
  return rows;
}

async function buildShopWorkbook() {
  const shopRows = await parseShopRows();
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add("ショップ現況監査");
  addGuideSheet(
    workbook,
    "BUYMA ショップ確認台帳 購入者版",
    "旧教材68件の2026-07-13時点の現況を入口にし、注文前の販売元・正規性・配送・返品・検品を更新します。",
    [
      "https://qa.buyma.com/shopper/prohibited-item/4007.html",
      "https://qa.buyma.com/shopper/order-to-delivery/4201.html",
    ],
    ["営業表示ありは、安全・正規品・BUYMA利用可・日本配送可の保証ではありません。注文ごとに再確認してください。"],
  );

  const headers = [
    "No.", "原教材ショップ名", "原教材の国", "現況分類", "詳細状態", "現行URL", "2026-07-13時点メモ", "現在のショップ名", "現在の国", "運営会社", "実販売元", "正規取扱根拠URL", "提携店・市場型", "BUYMA禁止先確認日", "購入証明", "日本・検品者へ配送", "現物検品経路", "税・関税", "決済・請求主体", "返品・返金", "証拠保管先", "最終判断", "判断理由", "次回確認日", "確認者", "変更履歴",
  ];
  const lastRow = 92;
  sheet.getRange("A4:Z4").values = [headers];
  styleTitle(sheet, "Z", "BUYMA ショップ確認台帳 購入者版", "旧68件は推薦リストではありません。確認日と根拠を更新し、注文直前に再確認します。");
  styleGrid(sheet, "Z", lastRow, []);
  setWidths(sheet, [8, 22, 16, 20, 22, 34, 40, 22, 16, 22, 22, 34, 18, 18, 18, 22, 22, 18, 22, 24, 26, 14, 28, 13, 14, 32], lastRow);

  const values = shopRows.map((row) => [
    row.no,
    row.oldName,
    row.oldCountry,
    row.status,
    row.rawStatus,
    row.url,
    row.note,
    "",
    "",
    "",
    "",
    "",
    "",
    new Date("2026-07-13"),
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    row.status === "閉鎖" || row.status === "除外" ? "除外" : "未確認",
    "",
    "",
    "",
    "",
  ]);
  sheet.getRange("A5:Z72").values = values;
  sheet.getRange("A73:A92").values = Array.from({ length: 20 }, () => [null]);
  sheet.getRange("D73:D92").values = Array.from({ length: 20 }, () => ["未確認"]);
  sheet.getRange("V73:V92").values = Array.from({ length: 20 }, () => ["未確認"]);
  sheet.getRange("D5:D92").dataValidation = { rule: { type: "list", values: ["未確認", "営業表示あり", "URL・名称・運営変更", "要再確認", "閉鎖", "除外"] } };
  sheet.getRange("M5:M92").dataValidation = { rule: { type: "list", values: ["未確認", "単独販売", "提携店型", "マーケットプレイス", "不明"] } };
  sheet.getRange("V5:V92").dataValidation = { rule: { type: "list", values: ["未確認", "使用可候補", "保留", "除外"] } };
  sheet.getRange("N5:N92").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("X5:X92").format.numberFormat = "yyyy-mm-dd";
  addStatusFormatting(sheet.getRange("D5:D92"));
  addStatusFormatting(sheet.getRange("V5:V92"));

  const order = workbook.worksheets.add("注文前確認");
  const orderHeaders = ["管理番号", "ショップNo.", "商品URL", "商品・型番", "実販売元", "在庫確認日時", "価格・通貨", "送料", "税・関税負担", "購入証明", "返品期限・条件", "検品者・場所", "追跡・補償", "BUYMA禁止先確認", "最終判断", "確認者", "証拠保管先", "備考"];
  order.getRange("A4:R4").values = [orderHeaders];
  styleTitle(order, "R", "ショップ注文前確認", "同じショップでも商品・販売元・配送・返品条件は注文ごとに変わります。");
  styleGrid(order, "R", 204, []);
  setWidths(order, [13, 11, 34, 22, 22, 18, 18, 14, 18, 18, 24, 22, 18, 20, 14, 14, 28, 30], 204);
  order.getRange("O5:O204").dataValidation = { rule: { type: "list", values: ["未確認", "注文可", "保留", "除外"] } };
  order.getRange("F5:F204").format.numberFormat = "yyyy-mm-dd hh:mm";
  addStatusFormatting(order.getRange("O5:O204"));

  await saveAndVerify(
    workbook,
    "BUYMA_ショップ確認台帳_購入者版.xlsx",
    [
      { sheet: "ショップ現況監査", range: "A1:Z12" },
      { sheet: "注文前確認", range: "A1:R11" },
      { sheet: "使い方", range: "A1:B12" },
    ],
    [
      { sheet: "ショップ現況監査", range: "A4:Z8" },
      { sheet: "注文前確認", range: "A4:R7" },
    ],
  );
}

await buildProfitWorkbook();
await buildListingWorkbook();
await buildDomesticWorkbook();
await buildOverseasWorkbook();
await buildDirectWorkbook();
await buildVipWorkbook();
await buildShopWorkbook();

console.log("ALL ATTACHMENTS BUILT");
