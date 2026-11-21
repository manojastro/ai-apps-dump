const fs = require("fs");
const path = require("path");

function materialize(target, dest) {
  const resolved = path.resolve(path.dirname(dest), String(target));
  fs.cpSync(resolved, dest, { recursive: true, force: true });
}

fs.symlinkSync = function symlinkSync(target, dest) {
  materialize(target, dest);
};

fs.symlink = function symlink(target, dest, type, cb) {
  if (typeof type === "function") cb = type;
  try {
    materialize(target, dest);
    if (cb) cb(null);
  } catch (err) {
    if (cb) cb(err);
    else throw err;
  }
};

if (fs.promises) {
  fs.promises.symlink = async function symlink(target, dest) {
    materialize(target, dest);
  };
}
