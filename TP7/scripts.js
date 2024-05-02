/**
 * delete the row on which the btn remove is.
 * @param {string} btn - the id of the btn
 */
// Fonction pour supprimer une carte
function Remove(btn) {
    const card = btn.closest('.card');
    card.parentNode.removeChild(card);
}
function addBook() {
    const last_id = parseInt($("#book_on_sale .card:last").attr("data-id") || "0");
    const newBookName = $("#new-book-name").val();
    const newBookAuthor = $("#new-book-author").val();
    const newBookPrice = $("#new-book-price").val();

    if (!newBookName || !newBookAuthor || !newBookPrice) {
        alert("All fields must be filled out");
        return;
    }

    const newCard = `
    <div class="card" data-id="${last_id + 1}" id="card-${last_id + 1}" draggable="true">
        <div class="card-body">
            <h5 class="card-title">${newBookName}</h5>
            <p class="card-text">${newBookAuthor}</p>
            <p class="card-text">Price: ${newBookPrice}€</p>
            <button class="btn btn-sm btn-danger" onclick="Remove(this)">Delete</button>
        </div>
    </div>
    `;

    $("#book_on_sale").append(newCard);
    addBehaviorToCard(document.getElementById(`card-${last_id + 1}`));

}


$("#book-form").submit(function(e) {
    e.preventDefault();
});

// Guide pour le drag&drop : https://www.w3schools.com/html/html5_draganddrop.asp


const addBehaviorToCard = (card) => {
    if (!card.id) {
        card.id = window.crypto.randomUUID()
    }

    // https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragstart_event
    card.addEventListener('dragstart', (event) => {
        event.dataTransfer.setData("card-id", event.target.id)
    })

    // https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragend_event
    card.addEventListener('dragend', (event) => {
        event.preventDefault()
    })
}

const addBehaviorToPanel = (panel) => {
    // https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragover_event
    panel.addEventListener('dragover', (event) => {
        event.preventDefault()
    })


    

    panel.addEventListener('drop', (event) => {
        event.preventDefault();  
        const draggedCardId = event.dataTransfer.getData("card-id");
        const draggedCard = document.getElementById(draggedCardId);
        if (draggedCard && event.target.classList.contains('col')) {  
            event.target.appendChild(draggedCard);
        }
    });
}

const main = () => {
    const cards = document.querySelectorAll(".card")
    cards.forEach((card) => {
        card.setAttribute('draggable', true)
    })
    cards.forEach(addBehaviorToCard)

    const panels = document.querySelectorAll(".col.bg-light.border")
    panels.forEach(addBehaviorToPanel)
}

document.addEventListener('DOMContentLoaded', main)
