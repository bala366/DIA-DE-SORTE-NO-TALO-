package com.diadesorte.talov1;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.pdf.PdfDocument;
import android.net.Uri;
import android.view.*;
import android.widget.*;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import org.json.*;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public class MainActivity extends Activity {

    static final int PICK_TXT = 101;
    static final int SAVE_PDF = 102;

    final ExecutorService executor = Executors.newSingleThreadExecutor();

    Button importar, gerar, pdf;
    TextView status, saida;
    ProgressBar progresso;

    String historicoTexto;
    Resultado resultado;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        montarTela();
    }

    void montarTela() {
        ScrollView scroll = new ScrollView(this);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(22, 22, 22, 50);
        root.setBackgroundColor(Color.rgb(255, 255, 245));

        scroll.addView(root);

        TextView titulo = new TextView(this);
        titulo.setText("★ DIA DE SORTE\\nENGROSSANDO O TALO V1");
        titulo.setTextSize(24);
        titulo.setTextColor(Color.WHITE);
        titulo.setGravity(Gravity.CENTER);
        titulo.setPadding(18, 28, 18, 28);
        titulo.setBackgroundColor(Color.rgb(22, 139, 80));

        root.addView(titulo, new LinearLayout.LayoutParams(-1, -2));

        TextView sub = new TextView(this);
        sub.setText("Mesmo motor Python do Pydroid • perímetro e repetidas aprendidos • quina pode • 6/7 elimina");
        sub.setTextSize(14);
        sub.setPadding(0, 18, 0, 14);
        root.addView(sub);

        importar = botao("IMPORTAR HISTÓRICO TXT");
        gerar = botao("GERAR JOGO");
        pdf = botao("GERAR PDF");

        gerar.setEnabled(false);
        pdf.setEnabled(false);

        root.addView(importar);
        root.addView(gerar);

        progresso = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progresso.setMax(100);
        root.addView(progresso, new LinearLayout.LayoutParams(-1, 22));

        status = new TextView(this);
        status.setText("Aguardando o histórico do Dia de Sorte.");
        status.setPadding(0, 12, 0, 12);
        root.addView(status);

        root.addView(pdf);

        saida = new TextView(this);
        saida.setTextSize(13);
        saida.setTextIsSelectable(true);
        saida.setPadding(0, 18, 0, 40);
        root.addView(saida);

        importar.setOnClickListener(v -> escolherArquivo());
        gerar.setOnClickListener(v -> executarMotor());
        pdf.setOnClickListener(v -> escolherDestinoPdf());

        setContentView(scroll);
    }

    Button botao(String texto) {
        Button b = new Button(this);
        b.setText(texto);
        b.setTextSize(16);
        return b;
    }

    void escolherArquivo() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("text/*");
        startActivityForResult(i, PICK_TXT);
    }

    void escolherDestinoPdf() {
        if (resultado == null) return;

        Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("application/pdf");
        i.putExtra(Intent.EXTRA_TITLE, "DIA_DE_SORTE_ENGROSSANDO_TALO_V1.pdf");
        startActivityForResult(i, SAVE_PDF);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            return;
        }

        if (requestCode == PICK_TXT) {
            carregarHistorico(data.getData());
        } else if (requestCode == SAVE_PDF) {
            salvarPdf(data.getData());
        }
    }

    void carregarHistorico(Uri uri) {
        bloquear(true);
        status.setText("Lendo histórico...");

        executor.execute(() -> {
            try {
                historicoTexto = lerTexto(uri);

                runOnUiThread(() -> {
                    bloquear(false);
                    gerar.setEnabled(true);
                    progresso.setProgress(100);
                    status.setText("Histórico carregado. Clique em GERAR JOGO.");
                    saida.setText("");
                });

            } catch (Throwable t) {
                runOnUiThread(() -> mostrarErro(t));
            }
        });
    }

    String lerTexto(Uri uri) throws Exception {
        try (
            InputStream in = getContentResolver().openInputStream(uri);
            ByteArrayOutputStream out = new ByteArrayOutputStream()
        ) {
            byte[] buffer = new byte[8192];
            int n;

            while ((n = in.read(buffer)) >= 0) {
                out.write(buffer, 0, n);
            }

            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    void executarMotor() {
        if (historicoTexto == null) return;

        bloquear(true);
        progresso.setProgress(10);
        status.setText("Executando o mesmo motor Python do Pydroid...");
        saida.setText("");

        executor.execute(() -> {
            try {
                Python py = Python.getInstance();
                PyObject modulo = py.getModule("motor_dia_de_sorte_v1");

                runOnUiThread(() -> {
                    progresso.setProgress(35);
                    status.setText("Estudando perímetro e repetidas...");
                });

                String json = modulo.callAttr("executar_texto", historicoTexto).toString();

                runOnUiThread(() -> {
                    progresso.setProgress(70);
                    status.setText("Engrossando o talo final...");
                });

                resultado = Resultado.fromJson(json);

                runOnUiThread(() -> {
                    bloquear(false);
                    pdf.setEnabled(true);
                    progresso.setProgress(100);
                    status.setText("Análise concluída.");
                    saida.setText(resultado.resumo());
                });

            } catch (Throwable t) {
                runOnUiThread(() -> mostrarErro(t));
            }
        });
    }

    void salvarPdf(Uri uri) {
        if (resultado == null) return;

        try (OutputStream os = getContentResolver().openOutputStream(uri)) {

            PdfDocument doc = new PdfDocument();

            PdfDocument.Page page = doc.startPage(
                new PdfDocument.PageInfo.Builder(595, 842, 1).create()
            );

            Canvas c = page.getCanvas();
            Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);

            p.setColor(Color.rgb(22, 139, 80));
            p.setTextSize(21);
            p.setFakeBoldText(true);

            c.drawText(
                "DIA DE SORTE — ENGROSSANDO O TALO V1",
                26,
                38,
                p
            );

            p.setTextSize(10);
            p.setFakeBoldText(false);
            p.setColor(Color.DKGRAY);

            c.drawText(
                "Mesmo motor Python do Pydroid",
                26,
                56,
                p
            );

            HashSet<Integer> jogo = new HashSet<>();
            HashSet<Integer> repetidas = new HashSet<>();

            for (int n : resultado.jogo) jogo.add(n);
            for (int n : resultado.repetidas) repetidas.add(n);

            int sx = 52;
            int sy = 104;
            int dx = 72;
            int dy = 52;
            int rr = 17;

            for (int n = 1; n <= 31; n++) {
                int idx = n - 1;
                int row = idx / 7;
                int col = idx % 7;

                float x = sx + col * dx;
                float y = sy + row * dy;

                boolean selecionado = jogo.contains(n);
                boolean repetida = repetidas.contains(n);

                if (repetida) {
                    p.setColor(Color.rgb(244, 197, 66));
                } else if (selecionado) {
                    p.setColor(Color.rgb(22, 139, 80));
                } else {
                    p.setColor(Color.rgb(232, 232, 222));
                }

                c.drawCircle(x, y, rr, p);

                p.setTextSize(10);
                p.setFakeBoldText(true);
                p.setColor(
                    selecionado ? Color.WHITE : Color.rgb(70, 70, 70)
                );

                String txt = Resultado.fmt(n);

                c.drawText(
                    txt,
                    x - p.measureText(txt) / 2,
                    y + 4,
                    p
                );
            }

            p.setFakeBoldText(false);
            p.setColor(Color.BLACK);
            p.setTextSize(9);

            int y = 390;

            for (String linha : resultado.resumo().split("\\n")) {
                if (y > 817) break;

                c.drawText(linha, 26, y, p);
                y += 12;
            }

            doc.finishPage(page);
            doc.writeTo(os);
            doc.close();

            status.setText("PDF gerado com sucesso.");

        } catch (Throwable t) {
            mostrarErro(t);
        }
    }

    void bloquear(boolean sim) {
        importar.setEnabled(!sim);
        gerar.setEnabled(!sim && historicoTexto != null);

        if (sim) {
            pdf.setEnabled(false);
            progresso.setProgress(0);
        }
    }

    void mostrarErro(Throwable t) {
        bloquear(false);
        status.setText("Erro: " + t.getMessage());

        new AlertDialog.Builder(this)
            .setTitle("Erro")
            .setMessage(String.valueOf(t))
            .setPositiveButton("OK", null)
            .show();
    }
}

class Resultado {

    int perimetro;
    int qtdRepetidas;
    int primeiroConcurso;
    int ultimoConcurso;

    int[] ultimoResultado;
    String ultimoMes;

    int[] jogo;
    int[] repetidas;
    int[] novas;

    String mesSorte;

    int qtd2;
    int qtd3;
    int qtd4;
    int qtd5;

    int ternos30;
    int ternos20;
    int ternos10;
    int ternos5;

    int[] ternosBlocos;
    int[] quadrasBlocos;
    int[] quinasBlocos;
    double[] pontosBlocos;

    double slopeBlocos;
    double crescimento;
    double score;

    static Resultado fromJson(String texto) throws Exception {
        JSONObject o = new JSONObject(texto);

        Resultado r = new Resultado();

        r.perimetro = o.getInt("perimetro");
        r.qtdRepetidas = o.getInt("qtd_repetidas");

        r.primeiroConcurso = o.getInt("primeiro_concurso_perimetro");
        r.ultimoConcurso = o.getInt("ultimo_concurso");

        r.ultimoResultado = ints(o.getJSONArray("ultimo_resultado"));
        r.ultimoMes = o.optString("ultimo_mes", "");

        r.jogo = ints(o.getJSONArray("jogo"));
        r.repetidas = ints(o.getJSONArray("repetidas"));
        r.novas = ints(o.getJSONArray("novas"));

        r.mesSorte = o.getJSONObject("mes_sorte").getString("mes");

        r.qtd2 = o.getInt("qtd2");
        r.qtd3 = o.getInt("qtd3");
        r.qtd4 = o.getInt("qtd4");
        r.qtd5 = o.getInt("qtd5");

        r.ternos30 = o.getInt("ternos30");
        r.ternos20 = o.getInt("ternos20");
        r.ternos10 = o.getInt("ternos10");
        r.ternos5 = o.getInt("ternos5");

        r.ternosBlocos = ints(o.getJSONArray("ternos_blocos"));
        r.quadrasBlocos = ints(o.getJSONArray("quadras_blocos"));
        r.quinasBlocos = ints(o.getJSONArray("quinas_blocos"));
        r.pontosBlocos = doubles(o.getJSONArray("pontos_blocos"));

        r.slopeBlocos = o.getDouble("slope_blocos");
        r.crescimento = o.getDouble("crescimento_blocos");
        r.score = o.getDouble("score");

        return r;
    }

    static int[] ints(JSONArray a) throws Exception {
        int[] r = new int[a.length()];

        for (int i = 0; i < a.length(); i++) {
            r[i] = a.getInt(i);
        }

        return r;
    }

    static double[] doubles(JSONArray a) throws Exception {
        double[] r = new double[a.length()];

        for (int i = 0; i < a.length(); i++) {
            r[i] = a.getDouble(i);
        }

        return r;
    }

    static String fmt(int n) {
        return String.format(Locale.US, "%02d", n);
    }

    static String grupo(int[] a) {
        int[] b = a.clone();
        Arrays.sort(b);

        StringBuilder s = new StringBuilder();

        for (int n : b) {
            if (s.length() > 0) s.append(" ");
            s.append(fmt(n));
        }

        return s.toString();
    }

    String resumo() {
        StringBuilder s = new StringBuilder();

        s.append("DIA DE SORTE — ENGROSSANDO O TALO V1\\n");
        s.append("Perímetro campeão: ").append(perimetro).append("\\n");
        s.append("Repetidas aprendidas: ").append(qtdRepetidas).append("\\n");
        s.append("Início do perímetro: ").append(primeiroConcurso).append("\\n");
        s.append("Último concurso: ").append(ultimoConcurso).append("\\n");
        s.append("Último resultado: ").append(grupo(ultimoResultado)).append("\\n");
        s.append("Último mês: ").append(ultimoMes).append("\\n\\n");

        s.append("JOGO FUTURO:\\n");
        s.append(grupo(jogo)).append("\\n\\n");

        s.append("Repetidas: ").append(grupo(repetidas)).append("\\n");
        s.append("Novas: ").append(grupo(novas)).append("\\n");
        s.append("Mês da Sorte: ").append(mesSorte).append("\\n\\n");

        s.append("Duques: ").append(qtd2).append("\\n");
        s.append("Ternos: ").append(qtd3).append("\\n");
        s.append("Quadras: ").append(qtd4).append("\\n");
        s.append("Quinas: ").append(qtd5).append("\\n");
        s.append("6 acertos: 0\\n");
        s.append("7 acertos: 0\\n\\n");

        s.append("Ternos 30/20/10/5: ")
            .append(ternos30).append(" / ")
            .append(ternos20).append(" / ")
            .append(ternos10).append(" / ")
            .append(ternos5).append("\\n\\n");

        s.append("Ternos por bloco: ")
            .append(Arrays.toString(ternosBlocos))
            .append("\\n");

        s.append("Quadras por bloco: ")
            .append(Arrays.toString(quadrasBlocos))
            .append("\\n");

        s.append("Quinas por bloco: ")
            .append(Arrays.toString(quinasBlocos))
            .append("\\n");

        s.append("Pontos do talo: ")
            .append(Arrays.toString(pontosBlocos))
            .append("\\n\\n");

        s.append("Slope: ")
            .append(String.format(Locale.US, "%+.4f", slopeBlocos))
            .append("\\n");

        s.append("Crescimento: ")
            .append(String.format(Locale.US, "%+.2f", crescimento))
            .append("\\n");

        s.append("Score: ")
            .append(String.format(Locale.US, "%.2f", score))
            .append("\\n");

        return s.toString();
    }
}
