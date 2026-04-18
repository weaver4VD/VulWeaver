

import SpliceOne from './SpliceOne.js';


var Remove = function (array, item, callback, context)
{
    if (context === undefined) { context = array; }

    var index;
    if (!Array.isArray(item))
    {
        index = array.indexOf(item);

        if (index !== -1)
        {
            SpliceOne(array, index);

            if (callback)
            {
                callback.call(context, item);
            }

            return item;
        }
        else
        {
            return null;
        }
    }

    var itemLength = item.length - 1;

    while (itemLength >= 0)
    {
        var entry = item[itemLength];

        index = array.indexOf(entry);

        if (index !== -1)
        {
            SpliceOne(array, index);

            if (callback)
            {
                callback.call(context, entry);
            }
        }
        else
        {
            item.pop();
        }

        itemLength--;
    }

    return item;
};

export default Remove;
