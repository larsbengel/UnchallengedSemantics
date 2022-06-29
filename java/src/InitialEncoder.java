import org.tweetyproject.arg.dung.semantics.Extension;
import org.tweetyproject.arg.dung.syntax.Argument;
import org.tweetyproject.arg.dung.syntax.DungTheory;
import org.tweetyproject.commons.util.Pair;
import org.tweetyproject.logics.pl.sat.SatSolver;
import org.tweetyproject.logics.pl.syntax.*;

import java.util.Collection;
import java.util.HashSet;
import java.util.List;

public class InitialEncoder {

    private DungTheory theory;

    public InitialEncoder(DungTheory theory) {
        this.theory = theory;
    }

    private Collection<PlFormula> transformToClauses (PlFormula formula) {
        Collection<PlFormula> clauses = formula.toCnf();
        System.out.println(clauses);
        return clauses;
    }

    public boolean solve(Collection<PlFormula> clauses) {
        Pair<String, List<PlFormula>> re = SatSolver.convertToDimacs(clauses);
        String output = re.getFirst();
        //TODO call solver and extract result
        return true;
    }

    public Collection<PlFormula> conflictFree(Collection<Argument> S) {
        Collection<PlFormula> result = new HashSet<>();
        for (Argument a: S) {
            for (Argument b: S) {
                result.add(new Negation(atom(a, b)));
            }
        }
        return result;
    }

    public boolean isUnattackedSet(Collection<Argument> S) {
        return S.size() == 1 && this.theory.getAttackers(S).isEmpty();
    }

    public Collection<PlFormula> encodeUnchallengedSet(Collection<Argument> S) {
        Collection<PlFormula> result = this.encodeInitialSet(S);
        //TODO
        return result;
    }

    public Collection<PlFormula> encodeInitialSet(Collection<Argument> S) {
        Collection<PlFormula> result = this.conflictFree(S);
        for (Argument a: S) {
            Collection<PlFormula> formulas = new HashSet<>();
            for (Argument b : this.theory.getAttackers(S)) {
                Collection<PlFormula> atoms = new HashSet<>();
                atoms.add(atom(a, b));
                for (Argument c : S) {
                    if (c != a) {
                        atoms.add(new Negation(atom(c, b)));
                    }
                }
                formulas.add(new Conjunction(atoms));
            }
            PlFormula formula = new Disjunction(formulas);result.addAll(this.transformToClauses(formula));
        }
        return result;
    }

    private Proposition atom(Argument a, Argument b) {
        return new Proposition("r_{" + a.getName() + "," + b.getName() + "}");
    }
}
