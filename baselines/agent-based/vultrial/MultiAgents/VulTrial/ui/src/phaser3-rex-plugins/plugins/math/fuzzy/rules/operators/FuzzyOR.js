import FuzzyCompositeTerm from './FuzzyCompositeTerm.js';


class FuzzyOR extends FuzzyCompositeTerm {
	constructor() {
		const terms = Array.from(arguments);
		super(terms);
	}

	getDegreeOfMembership() {
		const terms = this.terms;
		let maxDOM = -Infinity;
		for (let i = 0, l = terms.length; i < l; i++) {
			const currentDOM = terms[i].getDegreeOfMembership();
			if (currentDOM > maxDOM) {
				maxDOM = currentDOM;
			}

		}

		return maxDOM;
	}

}

export default FuzzyOR;
