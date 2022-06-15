import org.tweetyproject.arg.dung.parser.TgfParser;
import org.tweetyproject.arg.dung.semantics.Extension;
import org.tweetyproject.arg.dung.syntax.Argument;
import org.tweetyproject.arg.dung.syntax.DungTheory;
import org.tweetyproject.commons.util.Pair;
import org.tweetyproject.logics.pl.sat.SatSolver;
import org.tweetyproject.logics.pl.syntax.Conjunction;
import org.tweetyproject.logics.pl.syntax.PlFormula;

import java.io.IOException;
import java.util.Collection;
import java.util.List;

public class Main {
    public static void main(String[] args) throws IOException {
        TgfParser parser = new TgfParser();
        DungTheory theory = parser.parseBeliefBaseFromFile("example.tgf");
        Extension<DungTheory> ext = new Extension<>();
        ext.add(new Argument("1"));
        ext.add(new Argument("3"));


        Solver solver = new Solver(theory, ext);
        Collection<PlFormula> clauses = solver.solve();
        System.out.println(clauses);
        Pair<String, List<PlFormula>> re = SatSolver.convertToDimacs(clauses);
        String output = re.getFirst();
        System.out.println(output);

        System.out.println(theory.prettyPrint());

    }
}
