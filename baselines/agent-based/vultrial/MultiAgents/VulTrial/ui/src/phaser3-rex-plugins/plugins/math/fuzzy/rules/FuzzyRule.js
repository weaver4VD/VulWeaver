
class FuzzyRule {
	constructor(antecedent, consequence) {
		this.antecedent = antecedent;
		this.consequence = consequence;

	}

	initConsequence() {
		this.consequence.clearDegreeOfMembership();
		return this;
	}

	evaluate() {
		this.consequence.updateDegreeOfMembership(this.antecedent.getDegreeOfMembership());
		return this;

	}
}

export default FuzzyRule;
