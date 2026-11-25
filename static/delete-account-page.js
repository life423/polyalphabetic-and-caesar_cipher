import { mountAccountDeletion } from "./account-deletion.js";
mountAccountDeletion(document.getElementById("deletion-form-container"), {
  onDeleted: () => {
    document.getElementById("deletion-request").hidden = true;
    document.getElementById("deletion-success").hidden = false;
    document.getElementById("deleted-title").focus();
  },
});
