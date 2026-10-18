import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const buildDir = path.resolve(process.argv[2]);
const data = JSON.parse(await fs.readFile(path.join(buildDir, 'workbook-data.json'), 'utf8'));
const workbook = Workbook.create();
for (const [name, {columns, rows}] of Object.entries(data)) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  if (name !== 'data_notes') sheet.freezePanes.freezeColumns(2);
  sheet.getRangeByIndexes(0, 0, 1, columns.length).values = [columns];
  for (let offset = 0; offset < rows.length; offset += 4000) {
    const block = rows.slice(offset, offset + 4000).map(row => row.map((value, index) =>
      columns[index] === 'purchase_date' ? Date.parse(`${value}T00:00:00Z`) / 86400000 + 25569 : value));
    sheet.getRangeByIndexes(offset + 1, 0, block.length, columns.length).values = block;
  }
  const used = sheet.getRangeByIndexes(0, 0, Math.min(rows.length + 1, 25), columns.length);
  used.format.font = {name:'Arial',size:10,color:'#172B34'};
  used.format.rowHeight = 20;
  used.format.columnWidthPx = 190;
  const header = sheet.getRangeByIndexes(0,0,1,columns.length);
  header.format.fill = '#0F766E';
  header.format.font = {name:'Arial',size:10,bold:true,color:'#FFFFFF'};
  header.format.rowHeight = 32;
  header.format.wrapText = true;
  header.format.horizontalAlignment = 'center';
  for(let index=0;index<columns.length;index++){
    const range=sheet.getRangeByIndexes(1,index,rows.length,1);
    const field=columns[index];
    if(field==='purchase_date') range.setNumberFormat('yyyy-mm-dd');
    else if(field.includes('value')) range.setNumberFormat('#,##0.00');
    else if(field==='delivery_days_sum') range.setNumberFormat('#,##0.000000');
  }
  if(name==='data_notes'){
    sheet.getRangeByIndexes(0,0,rows.length+1,1).format.columnWidthPx=220;
    sheet.getRangeByIndexes(0,1,rows.length+1,1).format.columnWidthPx=1000;
  }
}
workbook.recalculate();
console.log((await workbook.inspect({kind:'region',sheetId:'orders_daily',range:'A1:F5',maxChars:1800,tableMaxRows:5,tableMaxCols:6})).ndjson);
console.log((await workbook.inspect({kind:'match',sheetId:'orders_daily',range:'A1:N20',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:10},maxChars:1000})).ndjson);
for(const name of Object.keys(data)){
  const range=name==='data_notes'?'A1:B6':'A1:F10';
  const preview=await workbook.render({sheetName:name,range,scale:1,format:'png'});
  await fs.writeFile(path.join(buildDir,`${name}-preview.png`),new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(workbook)).save(path.join(buildDir,'olist-dashboard-sources.xlsx'));
console.log(JSON.stringify({output:path.join(buildDir,'olist-dashboard-sources.xlsx'),rows:Object.fromEntries(Object.entries(data).map(([k,v])=>[k,v.rows.length]))}));
