import org.tweetyproject.arg.dung.syntax.Argument;
import org.tweetyproject.arg.dung.syntax.DungTheory;
import org.tweetyproject.commons.util.SetTools;
import org.tweetyproject.logics.pl.syntax.PlFormula;

import java.util.Collection;

public class UCSolver {
    public UCSolver() {

    }

    public boolean verify(Collection<Argument> S, DungTheory theory) {
        InitialEncoder encoder = new InitialEncoder(theory);

        boolean any_subset_is_ua_or_uc_in_F = false;
        for (Collection<Argument> args: new SetTools<Argument>().subsets(S)) {
            if (encoder.isUnattackedSet(args)) {
                any_subset_is_ua_or_uc_in_F = true;
                break;
            }
            Collection<PlFormula> clauses = encoder.encodeUnchallengedSet(S);
            encoder.solve(clauses);
        }
    }
}
