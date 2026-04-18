import FuzzyCompositeTerm from './FuzzyCompositeTerm.js';


class FuzzyVERY extends FuzzyCompositeTerm {

	constructor(fuzzyTerm = null) {
		super([fuzzyTerm]);
	}

	clearDegreeOfMembership() {
		this.terms[0].clearDegreeOfMembership();
		return this;

	}

	getDegreeOfMembership() {
		const dom = this.terms[0].getDegreeOfMembership();
		return dom * dom;

	}

	updateDegreeOfMembership(value) {
		this.terms[0].updateDegreeOfMembership(value * value);
		return this;
	}

}

export default FuzzyVERY;
