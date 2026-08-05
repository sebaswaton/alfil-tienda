import assert from "node:assert/strict";
import test from "node:test";

import {
  canImportValidatedFile,
  canUploadValidatedZip,
  formatFileSize,
} from "../src/utils/productImport.js";


const file = { name: "productos.xlsx" };
const validPreview = {
  can_import: true,
  total_rows: 3,
  invalid_rows: 0,
};


test("enables import only for a complete valid preview", () => {
  assert.equal(canImportValidatedFile(file, validPreview, false), true);
  assert.equal(canImportValidatedFile(null, validPreview, false), false);
  assert.equal(canImportValidatedFile(file, null, false), false);
  assert.equal(
    canImportValidatedFile(file, { ...validPreview, can_import: false }, false),
    false,
  );
  assert.equal(
    canImportValidatedFile(file, { ...validPreview, invalid_rows: 1 }, false),
    false,
  );
  assert.equal(
    canImportValidatedFile(file, { ...validPreview, total_rows: 0 }, false),
    false,
  );
  assert.equal(canImportValidatedFile(file, validPreview, true), false);
});


test("enables ZIP upload only for a complete valid preview", () => {
  const preview = { can_upload: true, total_files: 4, invalid_files: 0 };
  assert.equal(canUploadValidatedZip(file, preview, false), true);
  assert.equal(canUploadValidatedZip(null, preview, false), false);
  assert.equal(canUploadValidatedZip(file, { ...preview, can_upload: false }, false), false);
  assert.equal(canUploadValidatedZip(file, { ...preview, invalid_files: 1 }, false), false);
  assert.equal(canUploadValidatedZip(file, { ...preview, total_files: 0 }, false), false);
  assert.equal(canUploadValidatedZip(file, preview, true), false);
});


test("formats ZIP and media sizes for the preview", () => {
  assert.equal(formatFileSize(512), "512 B");
  assert.equal(formatFileSize(2048), "2.0 KB");
  assert.equal(formatFileSize(2 * 1024 * 1024), "2.0 MB");
});
