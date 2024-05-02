
/**
 * delete the row on which the btn remove is.
 * @param {string} btn - the id of the btn
 */
function Remove(btn){
    const row = btn.parentNode.parentNode
    row.parentNode.removeChild(row);
}

/**
 * add a book.
 */
function addBook(){
    const last_id = parseInt($("#book_on_sale tbody tr:last td:first").text());
    const newBookName = $("#new-book-name");
    const newBookAuthor = $("#new-book-author");
    const newBookPrice = $("#new-book-price");
    if (
        !newBookName.val()
        || !newBookAuthor.val()
        || !newBookPrice.val()
    ) {return;}
    $("#book_on_sale > tbody:last-child").append(
        `
        <tr>
            <td>${last_id+1}</td>
            <td>${newBookName.val()}</td>
            <td>${newBookAuthor.val()}</td>
            <td>${newBookPrice.val()}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="Remove(this)">Delete</button>
            </td>
        </tr>
        `
    );
}

$("#book-form").submit(function(e) {
    e.preventDefault();
});