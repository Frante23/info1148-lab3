import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.List;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import javax.swing.*;
import grammar.*;
import grammar.parse.*;
import file.XMLCodec;
import gui.grammar.*;
import gui.grammar.parse.BruteParsePane;
import gui.environment.GrammarEnvironment;

/** Reabre los .jff reales y usa el CYK original de JFLAP tras convertir a FNC.
 * La transformación se hace en memoria: no altera la gramática entregada.
 * Renderiza componentes originales de JFLAP, sin imitar su interfaz.
 */
public class VerificarJFLAP {
    static Grammar cargar(Path root, boolean extended, String start) {
        String name="gramatica_"+(extended?"extendida":"base")+(start.equals("I")?"_instrucciones":"")+".jff";
        Grammar g=(Grammar)new XMLCodec().decode(root.resolve("gramaticas/"+name).toFile(),Map.of());
        if(!g.getStartVariable().equals("S")) throw new AssertionError(name+": inicio incorrecto");
        if(!GrammarChecker.isContextFreeGrammar(g)) throw new AssertionError(name+": no es GLC");
        return g;
    }
    static Grammar fnc(Grammar g) {
        UnitProductionRemover remover=new UnitProductionRemover();
        Grammar noUnit=remover.getUnitProductionlessGrammar(g,remover.getVariableDependencyGraph(g));
        noUnit.setStartVariable(g.getStartVariable());
        CNFConverter converter=new CNFConverter(noUnit);
        ArrayDeque<Production> pending=new ArrayDeque<>(Arrays.asList(noUnit.getProductions()));
        Set<Production> normal=new LinkedHashSet<>();
        while(!pending.isEmpty()) {
            Production p=pending.remove();
            if(converter.isChomsky(p)) normal.add(p);
            else pending.addAll(Arrays.asList(converter.replacements(p)));
        }
        Grammar result=new UnrestrictedGrammar();
        // CYK compara nombres completos. Conservamos los auxiliares B(n)
        // del convertidor para no imponer el límite de 26 letras del editor.
        result.addProductions(normal.toArray(new Production[0]));
        result.setStartVariable(g.getStartVariable());
        return result;
    }
    static void layout(Container c) {
        c.doLayout();
        for(Component child:c.getComponents()) if(child instanceof Container) layout((Container)child);
    }
    static void render(JComponent component, Path path, int w, int h) throws Exception {
        component.setVisible(true);component.setSize(w,h);layout(component);
        BufferedImage image=new BufferedImage(w*2,h*2,BufferedImage.TYPE_INT_RGB);
        Graphics2D g=image.createGraphics();g.setColor(Color.WHITE);g.fillRect(0,0,w*2,h*2);g.scale(2,2);
        component.paint(g);g.dispose();ImageIO.write(image,"png",path.toFile());
    }
    static void renderGrammar(Grammar g, Path output, String title) throws Exception {
        GrammarInputPane pane=new GrammarInputPane(g);
        pane.getTable().setFont(new Font("Monospaced",Font.PLAIN,18));
        pane.getTable().setRowHeight(30);
        pane.getTable().getTableHeader().setFont(new Font("SansSerif",Font.BOLD,16));
        JPanel wrap=new JPanel(new BorderLayout());
        JLabel label=new JLabel(title); label.setBorder(BorderFactory.createEmptyBorder(12,12,12,12));
        label.setFont(new Font("SansSerif",Font.BOLD,17));
        wrap.add(label,BorderLayout.NORTH);wrap.add(new JScrollPane(pane.getTable()),BorderLayout.CENTER);
        render(wrap,output,650,Math.max(710,g.getProductions().length*30+120));
    }
    static class VistaDerivacion extends BruteParsePane {
        VistaDerivacion(Grammar g) {super(new GrammarEnvironment(new GrammarInputPane(g)),g);}
        void mostrar(ParseNode answer,String input) {
            inputField.setText(input);treePanel.setAnswer(answer);
            while(!treePanel.next()) { }
        }
        JComponent arbol() {return treePanel;}
    }
    static ParseNode brute(Grammar g,String input) throws Exception {
        BruteParser parser=BruteParser.get(g,input); parser.start();
        long deadline=System.nanoTime()+15_000_000_000L;
        while(!parser.isFinished()) {
            if(System.nanoTime()>deadline) {parser.pause();throw new AssertionError("Tiempo excedido: "+input);}
            Thread.sleep(5);
        }
        if(parser.getAnswer()==null)throw new AssertionError("Sin derivación: "+input);
        return parser.getAnswer();
    }
    public static void main(String[] args) throws Exception {
        Path root=Paths.get(args.length>0?args[0]:".");
        Files.createDirectories(root.resolve("evidencias/jflap"));
        Map<String,Grammar> originals=new LinkedHashMap<>(),converted=new LinkedHashMap<>();
        for(boolean extended:new boolean[]{false,true})for(String start:new String[]{"S","I"}) {
            String key=(extended?"1":"0")+start;
            Grammar original=cargar(root,extended,start);
            originals.put(key,original);converted.put(key,fnc(original));
        }
        List<String> log=new ArrayList<>();
        log.add("JFLAP 7.1: XMLCodec + eliminación de unitarias + CNFConverter + CYKParser.");
        log.add("No se modifican los archivos .jff. La forma normal solo existe en memoria.");
        int count=0;
        for(String row:Files.readAllLines(root.resolve("evidencias/validaciones/entradas_jflap.tsv"),StandardCharsets.UTF_8).subList(1,
            Files.readAllLines(root.resolve("evidencias/validaciones/entradas_jflap.tsv"),StandardCharsets.UTF_8).size())) {
            String[] c=row.split("\t",-1);String key=c[2]+c[1];
            boolean result=new CYKParser(converted.get(key)).solve(c[3]);
            if(result!=c[4].equals("1"))throw new AssertionError(c[0]+": JFLAP discrepa para "+c[3]+"\n"+converted.get(key));
            log.add(c[0]+" | inicio="+c[1]+" | extendida="+c[2]+" | "+c[3]+" | "+(result?"ACEPTADA":"RECHAZADA"));
            count++;
        }
        // Brute force produce derivaciones sobre las producciones originales.
        Map<String,ParseNode> answers=new LinkedHashMap<>();
        for(String[] pair:new String[][]{{"0I","i=i+i#"},{"0I","si#"},{"1I","ti#"}}) {
            ParseNode answer=brute(originals.get(pair[0]),pair[1]);
            answers.put(pair[1],answer);
            List<String> steps=new ArrayList<>();
            for(ParseNode node=answer;node!=null;node=(ParseNode)node.getParent()) steps.add(node.getDerivation());
            Collections.reverse(steps);
            log.add("BRUTE "+pair[1]+": "+String.join(" => ",steps));
        }
        final Exception[] failure={null};
        SwingUtilities.invokeAndWait(()->{
            try {
                for(Map.Entry<String,Grammar> item:originals.entrySet()) {
                    String name=(item.getKey().charAt(0)=='1'?"extendida":"base")+(item.getKey().endsWith("I")?"_instrucciones":"");
                    renderGrammar(item.getValue(),root.resolve("evidencias/jflap/"+name+".png"),"JFLAP 7.1 | gramatica_"+name+".jff");
                }
                int imageIndex=0;
                for(Map.Entry<String,ParseNode> item:answers.entrySet()) {
                    VistaDerivacion view=new VistaDerivacion(originals.get(item.getKey().equals("ti#")?"1I":"0I"));
                    view.mostrar(item.getValue(),item.getKey());
                    boolean assignment=item.getKey().equals("i=i+i#");
                    render(view.arbol(),root.resolve("evidencias/jflap/derivacion_"+(++imageIndex)+".png"),assignment?650:450,assignment?440:330);
                }
            } catch(Exception ex) {failure[0]=ex;}
        });
        if(failure[0]!=null)throw failure[0];
        log.add("OK: "+count+" entradas contrastadas con CYK; 3 derivaciones con BruteParser; 4 archivos abiertos.");
        Files.write(root.resolve("evidencias/validaciones/jflap_resultados.txt"),log,StandardCharsets.UTF_8);
        System.out.println(log.get(log.size()-1));
        System.exit(0);
    }
}
