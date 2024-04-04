function confirmAndDelete(clickedElement) {
    if (confirm("Are you sure you want to delete this book?")) {
        clickedElement.parentElement.submit();
    }
}