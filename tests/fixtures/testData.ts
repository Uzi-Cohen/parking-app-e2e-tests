const BANNED = new Set([
  '12345678',
  '87654321',
  '11111111',
  '99999999',
  '00000000',
]);

function isSequential(digits: number[]): boolean {
  const ascending = digits.every(
    (d, i) => i === 0 || d === digits[i - 1] + 1,
  );
  const descending = digits.every(
    (d, i) => i === 0 || d === digits[i - 1] - 1,
  );
  return ascending || descending;
}

/**
 * Generates a random 8-digit license plate string that passes all
 * server-side and client-side validation rules:
 *  - Exactly 8 digits (0-9)
 *  - Not all identical digits
 *  - Not a strictly ascending or descending sequence
 *  - Not in the banned-patterns list
 */
export function randomPlate(): string {
  while (true) {
    let plate = '';
    for (let i = 0; i < 8; i++) {
      plate += Math.floor(Math.random() * 10).toString();
    }
    if (BANNED.has(plate)) continue;
    if (new Set(plate).size === 1) continue; // all identical digits
    const digits = plate.split('').map(Number);
    if (isSequential(digits)) continue;
    return plate;
  }
}

/**
 * Generates a unique slot identifier per test run, avoiding collisions
 * between concurrent tests (even though workers=1, we still isolate by
 * timestamp + random suffix).
 */
export function uniqueSlot(): string {
  const ts = Date.now();
  const rand = Math.floor(Math.random() * 10_000);
  return `E2E-${ts}-${rand}`;
}
