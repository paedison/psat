function setupPrintOnLoad() {
    window.addEventListener("load", function () {
        setTimeout(function () {
            window.print();
        }, 1000);
    });
}
