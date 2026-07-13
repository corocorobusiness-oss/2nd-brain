import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourceDir = "/private/tmp/buyma-notion-read/sheets";
const previewDir = path.resolve("プレビュー/原本確認");
const sourceNames = [
  "domestic.xlsx",
  "overseas.xlsx",
  "direct.xlsx",
  "recruit.xlsx",
  "vip.xlsx",
  "comments.xlsx",
];

await fs.mkdir(previewDir, { recursive: true });

for (const sourceName of sourceNames) {
  const input = await FileBlob.load(path.join(sourceDir, sourceName));
  const workbook = await SpreadsheetFile.importXlsx(input);
  const sheetSummary = await workbook.inspect({
    kind: "sheet",
    include: "id,name",
    maxChars: 8000,
  });
  console.log(`SOURCE ${sourceName}`);
  console.log(sheetSummary.ndjson);

  for (const sheet of workbook.worksheets.items) {
    const used = sheet.getUsedRange(true);
    if (!used) {
      console.log(`  SHEET ${sheet.name}: empty`);
      continue;
    }

    const region = await workbook.inspect({
      kind: "region",
      sheetId: sheet.name,
      range: used.address,
      maxChars: 2500,
      tableMaxRows: 8,
      tableMaxCols: 12,
      tableMaxCellChars: 80,
    });
    console.log(`  SHEET ${sheet.name} RANGE ${used.address}`);
    console.log(region.ndjson);

    const preview = await workbook.render({
      sheetName: sheet.name,
      autoCrop: "all",
      scale: 0.8,
      format: "png",
    });
    const safeSheetName = sheet.name.replace(/[\\/:*?"<>|]/g, "_");
    await fs.writeFile(
      path.join(previewDir, `${sourceName.replace(/\.xlsx$/, "")}_${safeSheetName}.png`),
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
}
