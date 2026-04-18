import FuzzySet from './FuzzySet.js';


class TriangularFuzzySet extends FuzzySet {
	constructor(left, midpoint, right) {

		super(midpoint);

		this.left = left;
		this.midpoint = midpoint;
		this.right = right;

	}

	computeDegreeOfMembership(value) {

		const midpoint = this.midpoint;
		const left = this.left;
		const right = this.right;

		if ((value >= left) && (value <= midpoint)) {
			const grad = 1 / (midpoint - left);
			return grad * (value - left);

		}
		if ((value > midpoint) && (value <= right)) {
			const grad = 1 / (right - midpoint);
			return grad * (right - value);

		}
		return 0;

	}
}

export default TriangularFuzzySet;
