import { sum } from "../src/script.js"

QUnit.test("add() adds numbers correctly", function(assert) {
    assert.equal(sum(2, 3), 5, "add(2, 3) should be 5");
    assert.equal(sum(-1, 1), 0, "add(-1, 1) should be 0");
});
