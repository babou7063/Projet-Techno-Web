
/**
 * delete the row on which the btn remove is.
 * @param {string} btn - the id of the btn
 */
function Remove(btn){

    const row = btn.parentNode.parentNode
    row.parentNode.removeChild(row);

}