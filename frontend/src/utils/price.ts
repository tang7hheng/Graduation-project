/**
 * 价格解析工具。
 * 从价格字符串中提取首个数值:取第一个数字,避免 "199-299" 被解析成 199299;
 * "面议" 等不含数字时返回 0。
 */
export function parsePrice(p: string): number {
  const m = (p || '').match(/\d+(?:\.\d+)?/)
  return m ? parseFloat(m[0]) : 0
}
