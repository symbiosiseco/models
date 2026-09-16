/**
 * 日期时间工具
 * 受 GPL v3.0 保护
 */
const DateTimeUtils = {

    _pad(n) {
        return n < 10 ? '0' + n : '' + n;
    },

    _toDate(date) {
        if (date instanceof Date) return date;
        if (typeof date === 'number') return new Date(date);
        if (typeof date === 'string') {
            const d = new Date(date.replace(/-/g, '/'));
            return isNaN(d.getTime()) ? null : d;
        }
        return null;
    },

    /**
     * 格式化日期
     * @param {Date|number|string} date
     * @param {string} pattern 支持 YYYY MM DD HH mm ss
     */
    format(date, pattern = 'YYYY-MM-DD HH:mm:ss') {
        const d = this._toDate(date);
        if (!d) return '';
        const map = {
            'YYYY': d.getFullYear(),
            'MM': this._pad(d.getMonth() + 1),
            'DD': this._pad(d.getDate()),
            'HH': this._pad(d.getHours()),
            'mm': this._pad(d.getMinutes()),
            'ss': this._pad(d.getSeconds()),
        };
        let result = pattern;
        for (const k in map) {
            result = result.replace(k, map[k]);
        }
        return result;
    },

    formatTime(timestamp) {
        return this.format(timestamp, 'HH:mm:ss');
    },

    formatDate(timestamp) {
        return this.format(timestamp, 'YYYY-MM-DD');
    },

    formatDateTime(timestamp) {
        return this.format(timestamp, 'YYYY-MM-DD HH:mm');
    },

    parse(dateStr) {
        return this._toDate(dateStr);
    },

    addMinutes(date, minutes) {
        const d = this._toDate(date);
        if (!d) return null;
        return new Date(d.getTime() + minutes * 60 * 1000);
    },

    addDays(date, days) {
        const d = this._toDate(date);
        if (!d) return null;
        return new Date(d.getTime() + days * 24 * 60 * 60 * 1000);
    },

    diffDays(date1, date2) {
        const d1 = this._toDate(date1);
        const d2 = this._toDate(date2);
        if (!d1 || !d2) return 0;
        return Math.round((d2.getTime() - d1.getTime()) / (24 * 60 * 60 * 1000));
    },

    isToday(date) {
        const d = this._toDate(date);
        if (!d) return false;
        const now = new Date();
        return d.getFullYear() === now.getFullYear()
            && d.getMonth() === now.getMonth()
            && d.getDate() === now.getDate();
    },

    isPast(date) {
        const d = this._toDate(date);
        return d ? d.getTime() < Date.now() : false;
    },

    isFuture(date) {
        const d = this._toDate(date);
        return d ? d.getTime() > Date.now() : false;
    },

    /**
     * 获取相对时间（如"3分钟前"）
     */
    getRelativeTime(date) {
        const d = this._toDate(date);
        if (!d) return '';
        const diff = Date.now() - d.getTime();
        const sec = Math.floor(diff / 1000);
        if (sec < 60) return `${sec}秒前`;
        const min = Math.floor(sec / 60);
        if (min < 60) return `${min}分钟前`;
        const hour = Math.floor(min / 60);
        if (hour < 24) return `${hour}小时前`;
        const day = Math.floor(hour / 24);
        if (day < 30) return `${day}天前`;
        return this.formatDate(d);
    },
};

window.DateTimeUtils = DateTimeUtils;