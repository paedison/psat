/* global CKEDITOR, django */
function initCkeditor(scope = document) {
  window.CKEDITOR_BASEPATH = '/static/ckeditor/ckeditor/';

  function runInitializers() {
    if (!window.CKEDITOR) {
      setTimeout(runInitializers, 100);
      return;
    }

    initializeCKEditor(scope);
    initializeCKEditorInInlinedForms();
  }
  
  runInitializers();

  function initializeCKEditor(scope = document) {
    const textAreas = Array.from(scope.querySelectorAll('textarea[data-type=ckeditortype]'));
    for (const t of textAreas) {
      if (
        t.getAttribute("data-processed") === "0" &&
        t.id.indexOf("__prefix__") === -1
      ) {
        t.setAttribute("data-processed", "1");
        const ext = JSON.parse(t.getAttribute("data-external-plugin-resources"));
        for (const [name, path, file] of ext) CKEDITOR.plugins.addExternal(name, path, file);
        CKEDITOR.replace(t.id, JSON.parse(t.getAttribute("data-config")));
      }
    }
  }

  function initializeCKEditorInInlinedForms() {
    if (typeof django === "object" && django.jQuery) {
      django.jQuery(document).on("formset:added", () => initializeCKEditor(scope))
    }
  }
}

window.addEventListener('load', () => initCkeditor(document));

document.body.addEventListener('initCkeditor', (e) => {
  const target = e.detail?.target || document;
  initCkeditor(target);
});

document.body.addEventListener('htmx:beforeRequest', () => {
  for (const instanceName in CKEDITOR.instances) {
    if (CKEDITOR.instances.hasOwnProperty(instanceName)) {
      CKEDITOR.instances[instanceName].destroy(true);
    }
  }
});
