/**
 * Load and list assessment profiles.
 */

const PROFILE_IDS = [
  "csharp",
  "java",
  "architecture",
  "frontend-angular",
  "frontend-react",
  "frontend-vue",
  "manager",
];

/**
 * Load a single profile by ID.
 * @param {string} id - Profile ID (e.g. 'csharp', 'java')
 * @returns {Promise<Object>}
 */
export async function loadProfile(id) {
  const base = import.meta.env.BASE_URL || "/";
  const path = `${base}profiles/${id}.json`;
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load profile: ${id}`);
  return res.json();
}

/**
 * Load all profiles (names only for the dropdown).
 * @returns {Promise<Array<{id: string, name: string}>>}
 */
export async function loadProfiles() {
  const profiles = [];
  for (const id of PROFILE_IDS) {
    try {
      const p = await loadProfile(id);
      profiles.push({ id, name: p.name || id });
    } catch {
      console.warn(`Could not load profile: ${id}`);
    }
  }
  return profiles;
}
