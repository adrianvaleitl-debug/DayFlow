export type TaskLike={done?:boolean};
export function taskProgress(tasks:TaskLike[]){const total=tasks.length;const completed=tasks.filter(task=>task.done).length;return{total,completed,remaining:total-completed,percentage:total?Math.round(completed/total*100):0}}
export function isDueOnDate(value:string|undefined,date:Date):boolean{if(!value)return false;const due=new Date(value+"T00:00:00");return !Number.isNaN(due.getTime())&&due.getFullYear()===date.getFullYear()&&due.getMonth()===date.getMonth()&&due.getDate()===date.getDate()}
