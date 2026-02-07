import FuzzySet from './FuzzySet.js';


class LeftShoulderFuzzySet extends FuzzySet {
	constructor(left, midpoint, right) {
		const representativeValue = (midpoint + left) / 2;
		super(representativeValue);

		this.left = left;
		this.midpoint = midpoint;
		this.right = right;

	}

	computeDegreeOfMembership(value) {
		const midpoint = this.midpoint;
		const left = this.left;
		const right = this.right;
		if ((value >= left) && (value <= midpoint)) {
			return 1;

		}
		if ((value > midpoint) && (value <= right)) {
			const grad = 1 / (right - midpoint);
			return grad * (right - value);

		}
		return 0;

	}
}

export default LeftShoulderFuzzySet;
