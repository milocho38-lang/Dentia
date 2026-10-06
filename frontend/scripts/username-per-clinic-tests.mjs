import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "../..");
const read = (relativePath) =>
  fs.readFileSync(path.join(root, relativePath), "utf8");

const login = read("frontend/components/auth/LoginForm.tsx");
const userForm = read("frontend/components/users/UserForm.tsx");
const userDetail = read("frontend/components/users/UserDetail.tsx");
const userList = read("frontend/components/users/UserList.tsx");
const platform = read("frontend/components/platform/PlatformCompanyPages.tsx");
const authTypes = read("frontend/types/auth.ts");
const userTypes = read("frontend/types/user.ts");
const platformTypes = read("frontend/types/platform.ts");

assert.match(login, /const \[identifier, setIdentifier\] = useState\(""\)/);
assert.match(login, /login\(\{\s*identifier: identifier\.trim\(\),\s*password,/s);
assert.match(login, /autoComplete="username"/);
assert.doesNotMatch(login, /type="email"[\s\S]*autoComplete="username"/);

assert.match(userForm, /const \[username, setUsername\]/);
assert.match(userForm, /username: username\.trim\(\)/);
assert.match(
  userForm,
  /editing && user && username === user\.username && username\.length > 100 \? 320 : 100/,
);
assert.match(userDetail, /"Nombre de usuario", user\.username/);
assert.match(userList, /@\{user\.username\}/);

assert.match(platform, /admin_username: ""/);
assert.match(platform, /input\("admin_username", "Nombre de usuario administrador"\)/);
assert.match(platform, /@\{user\.username\}/);

for (const [name, source] of [
  ["auth", authTypes],
  ["user", userTypes],
  ["platform", platformTypes],
]) {
  assert.match(source, /username: string;/, `${name} types must expose username`);
}
assert.match(authTypes, /interface LoginCredentials \{\s*identifier: string;/s);
assert.match(userTypes, /interface UserCreateInput \{[\s\S]*username: string;/);
assert.match(userTypes, /interface UserUpdateInput \{[\s\S]*username: string;/);
assert.match(platformTypes, /admin_username: string;/);

console.log(
  "username-per-clinic-tests OK: login, historical edit compatibility, user and platform forms",
);
