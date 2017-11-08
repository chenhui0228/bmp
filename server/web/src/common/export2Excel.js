/**
 * @desc:
 * @date: 2017/11/8 9:14
 * @author: 01107267 chenhui
 * @version:
 */
import XLSX from 'xlsx';
import XLSX_SAVE from  'file-saver'

function s2ab(s) {
  if(typeof ArrayBuffer !== 'undefined') {
    var buf = new ArrayBuffer(s.length);
    var view = new Uint8Array(buf);
    for (var i=0; i!=s.length; ++i) view[i] = s.charCodeAt(i) & 0xFF;
    return buf;
  } else {
    var buf = new Array(s.length);
    for (var i=0; i!=s.length; ++i) buf[i] = s.charCodeAt(i) & 0xFF;
    return buf;
  }
};

export default {
  export2Excel: function(_json, sheetName, bookName){
    var ws = XLSX.utils.json_to_sheet(_json);
    var wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
    var wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'binary' });
    XLSX_SAVE.saveAs(new Blob([s2ab(wbout)], { type: 'application/octet-stream' }), bookName+".xlsx");
  },
}
