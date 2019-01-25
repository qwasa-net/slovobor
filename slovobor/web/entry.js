require('./slovobor.js');
require('./slovobor.css');
require('./slovobor.svg');
require('./tg_logo.svg');
require('./favicon.svg');
require('./favicon.ico');

if (YANDEX_METRIKA_ID || GOOGLE_TRACKING_ID){
    require('./_trackers.js');
}