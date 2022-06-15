import org.tweetyproject.arg.dung.semantics.Extension;
import org.tweetyproject.arg.dung.syntax.Argument;
import org.tweetyproject.arg.dung.syntax.DungTheory;
import org.tweetyproject.logics.pl.syntax.*;

import java.util.Collection;
import java.util.HashSet;

public class Solver {
    private Collection<PlFormula> clauses;
    private DungTheory theory;
    private Extension<DungTheory> S;

    public Solver(DungTheory theory, Extension<DungTheory> ext) {
        this.theory = theory;
        clauses = new HashSet<>();
        this.S = ext;
    }

    public Collection<PlFormula> solve() {
        this.clauses = this.initial(this.S);
        return this.clauses;
    }

    private Proposition atom(Argument a, Argument b) {
        return new Proposition("r_{" + a.getName() + "," + b.getName() + "}");
    }

    public Collection<PlFormula> conflictFree(Extension<DungTheory> S) {
        Collection<PlFormula> result = new HashSet<>();
        for (Argument a: S) {
            for (Argument b: S) {
                result.add(new Negation(atom(a, b)));
            }
        }
        return result;
    }

    public Collection<PlFormula> admissible(Extension<DungTheory> S) {
        Collection<PlFormula> result = this.conflictFree(S);
        for (Argument a: this.theory.getAttackers(S)) {
            Collection<PlFormula> atoms = new HashSet<>();
            for (Argument b: S) {
                atoms.add(atom(b, a));
            }
            result.add(new Disjunction(atoms));
        }
        return result;
    }

    public Collection<PlFormula> notAttacking(Extension<DungTheory> X, Extension<DungTheory> Y) {
        Collection<PlFormula> result = new HashSet<>();
        for (Argument a: X) {
            for (Argument b: Y) {
                result.add(new Negation(atom(a, b)));
            }
        }
        return result;
    }

    public Collection<PlFormula> empty(Extension<DungTheory> S) {
        Collection<PlFormula> result = new HashSet<>();
        for (Argument a: S) {
            result.add(new Contradiction());
        }
        return result;
    }

    public Collection<PlFormula> notEmpty(Extension<DungTheory> S) {
        Collection<PlFormula> result = new HashSet<>();
        Collection<PlFormula> atoms = new HashSet<>();
        for (Argument a: S) {
            atoms.add(new Tautology());
        }
        result.add(new Disjunction(atoms));
        return result;
    }

    // TODO finish
    public Collection<PlFormula> initial(Extension<DungTheory> S) {
        Collection<PlFormula> result = this.admissible(S);
        for (Argument a: S) {
            Collection<PlFormula> formulas = new HashSet<>();
            for (Argument b: this.theory.getAttackers(S)) {
                Collection<PlFormula> atoms = new HashSet<>();
                atoms.add(atom(a, b));
                for (Argument c: S) {
                    if (c != a) {
                        atoms.add(new Negation(atom(c, b)));
                    }
                }
                formulas.add(new Conjunction(atoms));
            }
            PlFormula formula = new Disjunction(formulas);
            System.out.println(formula);
            System.out.println(formula.toCnf());
            System.out.println("===============");


        }
        return result;
    }

    public Collection<PlFormula> unattackedSet(Extension<DungTheory> S) {
        Collection<PlFormula> result = new HashSet<>();
        for (Argument a: this.theory.getAttackers(S)) {
            result.add(new Contradiction());
        }
        return result;
    }


}
