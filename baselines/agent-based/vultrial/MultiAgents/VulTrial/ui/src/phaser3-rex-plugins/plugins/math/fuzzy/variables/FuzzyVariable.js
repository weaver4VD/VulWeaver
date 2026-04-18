
class FuzzyVariable {
	constructor() {

		this.fuzzySets = [];

		this.minRange = Infinity;
		this.maxRange = - Infinity;

	}

	add(fuzzySet) {
		this.fuzzySets.push(fuzzySet);
		if (fuzzySet.left < this.minRange) {
			this.minRange = fuzzySet.left
		};
		if (fuzzySet.right > this.maxRange) {
			this.maxRange = fuzzySet.right;
		}

		return this;
	}

	remove(fuzzySet) {

		const fuzzySets = this.fuzzySets;

		const index = fuzzySets.indexOf(fuzzySet);
		fuzzySets.splice(index, 1);
		this.minRange = Infinity;
		this.maxRange = - Infinity;

		for (let i = 0, l = fuzzySets.length; i < l; i++) {

			const fuzzySet = fuzzySets[i];

			if (fuzzySet.left < this.minRange) {
				this.minRange = fuzzySet.left;
			}
			if (fuzzySet.right > this.maxRange) {
				this.maxRange = fuzzySet.right;
			}

		}

		return this;
	}

	fuzzify(value) {

		if (value < this.minRange || value > this.maxRange) {
			return;
		}

		const fuzzySets = this.fuzzySets;
		for (let i = 0, l = fuzzySets.length; i < l; i++) {
			const fuzzySet = fuzzySets[i];
			fuzzySet.degreeOfMembership = fuzzySet.computeDegreeOfMembership(value);

		}

		return this;
	}


	defuzzifyMaxAv() {
		const fuzzySets = this.fuzzySets;

		let bottom = 0;
		let top = 0;

		for (let i = 0, l = fuzzySets.length; i < l; i++) {
			const fuzzySet = fuzzySets[i];
			bottom += fuzzySet.degreeOfMembership;
			top += fuzzySet.representativeValue * fuzzySet.degreeOfMembership;
		}

		return (bottom === 0) ? 0 : (top / bottom);
	}

	defuzzifyCentroid(samples = 10) {

		const fuzzySets = this.fuzzySets;
		const stepSize = (this.maxRange - this.minRange) / samples;

		let totalArea = 0;
		let sumOfMoments = 0;

		for (let s = 1; s <= samples; s++) {
			const sample = this.minRange + (s * stepSize);

			for (let i = 0, l = fuzzySets.length; i < l; i++) {
				const fuzzySet = fuzzySets[i];
				const contribution = Math.min(fuzzySet.degreeOfMembership, fuzzySet.computeDegreeOfMembership(sample));
				totalArea += contribution;
				sumOfMoments += (sample * contribution);
			}

		}

		return (totalArea === 0) ? 0 : (sumOfMoments / totalArea);
	}

}

export default FuzzyVariable;
