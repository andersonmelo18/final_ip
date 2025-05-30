import csv
import os
from flask import Flask, render_template, url_for, request, redirect, flash

from google import genai

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'super secret key')  # Use env variable or default

# Initialize Gemini client using environment variable for API key
GENAI_API_KEY = os.getenv("GENAI_API_KEY", "AIzaSyD_iB6pRuTCdhadQ2fasOF5K5MhUZyKL_w")
client = genai.Client(api_key=GENAI_API_KEY)


def call_gemini_api(question):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=question
        )
        return response.text
    except Exception as e:
        return f"Erro ao chamar a API: {e}"


@app.route('/')
def ola():
    return render_template('index.html')


@app.route('/sobre-equipe')
def sobre_equipe():
    return render_template('sobre_equipe.html')


@app.route('/selecao')
def selecao():
    return render_template('selecao.html')


@app.route('/repeticao')
def repeticao():
    return render_template('repeticao.html')


@app.route('/vetores-matrizes')
def vetores_matrizes():
    return render_template('vetores_matrizes.html')


@app.route('/funcoes-procedimentos')
def funcoes_procedimentos():
    return render_template('funcoes_procedimentos.html')


@app.route('/tratamento')
def tratamento():
    return render_template('tratamento.html')


@app.route('/glossario')
def glossario():
    glossario_de_termos = []
    with open('bd_glossario.csv', 'r', newline='', encoding='utf-8') as arquivo:
        reader = csv.reader(arquivo, delimiter=';')
        for linha in reader:
            glossario_de_termos.append(linha)
    return render_template('glossario.html', glossario=glossario_de_termos)


@app.route('/novo-termo')
def novo_termo():
    return render_template('novo_termo.html')


@app.route('/criar_termo', methods=['POST'])
def criar_termo():
    termo = request.form['termo'].strip()
    definicao = request.form['definicao'].strip()

    if not termo or not definicao:
        flash('Termo e definição não podem estar vazios.', 'error')
        return redirect(url_for('novo_termo'))

    with open('bd_glossario.csv', 'a', newline='', encoding='utf-8') as arquivo:
        writer = csv.writer(arquivo, delimiter=';')
        writer.writerow([termo, definicao])

    flash(f'O termo "{termo}" foi adicionado ao glossário!', 'success')
    return redirect(url_for('glossario'))


@app.route('/deletar_termo', methods=['POST'])
def deletar_termo():
    termo_para_deletar = request.form['termo_para_deletar'].strip()
    if not termo_para_deletar:
        flash('Termo para deletar não pode estar vazio.', 'error')
        return redirect(url_for('glossario'))

    termos_atualizados = []
    try:
        with open('bd_glossario.csv', 'r', newline='', encoding='utf-8') as arquivo_leitura:
            reader = csv.reader(arquivo_leitura, delimiter=';')
            for linha in reader:
                if linha and linha[0] != termo_para_deletar:
                    termos_atualizados.append(linha)
        with open('bd_glossario.csv', 'w', newline='', encoding='utf-8') as arquivo_escrita:
            writer = csv.writer(arquivo_escrita, delimiter=';')
            writer.writerows(termos_atualizados)
        flash(f'O termo "{termo_para_deletar}" foi deletado do glossário!', 'success')
    except FileNotFoundError:
        flash('Erro: O arquivo do glossário não foi encontrado.', 'error')
    except Exception as e:
        flash(f'Ocorreu um erro ao deletar o termo: {e}', 'error')
    return redirect(url_for('glossario'))


@app.route('/alterar_termo/<termo>', methods=['GET'])
def alterar_termo(termo):
    termo = termo.strip()
    termo_encontrado = None
    try:
        with open('bd_glossario.csv', 'r', newline='', encoding='utf-8') as arquivo:
            reader = csv.reader(arquivo, delimiter=';')
            for linha in reader:
                if linha and linha[0] == termo:
                    termo_encontrado = linha
                    break
        if termo_encontrado is None:
            flash(f'Termo "{termo}" não encontrado.', 'error')
            return redirect(url_for('glossario'))
    except FileNotFoundError:
        flash('Arquivo do glossário não encontrado.', 'error')
        return redirect(url_for('glossario'))
    return render_template('alterar_termo.html', termo=termo_encontrado[0], definicao=termo_encontrado[1])


# New route to receive the edit form submission and update the term in CSV
@app.route('/salvar_termo_alterado', methods=['POST'])
def salvar_termo_alterado():
    termo_original = request.form['termo_original'].strip()
    termo_novo = request.form['termo'].strip()
    definicao_nova = request.form['definicao'].strip()

    if not termo_novo or not definicao_nova:
        flash('Termo e definição não podem estar vazios.', 'error')
        return redirect(url_for('alterar_termo', termo=termo_original))

    termos_atualizados = []
    termo_encontrado = False
    try:
        with open('bd_glossario.csv', 'r', newline='', encoding='utf-8') as arquivo_leitura:
            reader = csv.reader(arquivo_leitura, delimiter=';')
            for linha in reader:
                if linha:
                    if linha[0] == termo_original:
                        termos_atualizados.append([termo_novo, definicao_nova])
                        termo_encontrado = True
                    else:
                        termos_atualizados.append(linha)
        if not termo_encontrado:
            flash(f'Termo original "{termo_original}" não encontrado.', 'error')
            return redirect(url_for('glossario'))
        with open('bd_glossario.csv', 'w', newline='', encoding='utf-8') as arquivo_escrita:
            writer = csv.writer(arquivo_escrita, delimiter=';')
            writer.writerows(termos_atualizados)
        flash(f'O termo "{termo_original}" foi alterado para "{termo_novo}".', 'success')
    except FileNotFoundError:
        flash('Arquivo do glossário não encontrado.', 'error')
    except Exception as e:
        flash(f'Ocorreu um erro ao salvar a alteração: {e}', 'error')

    return redirect(url_for('glossario'))  # Redirect after saving changes


@app.route('/duvidas', methods=['GET', 'POST'])
def duvidas():
    resposta_gemini = None
    pergunta = None
    error = None
    if request.method == 'POST':
        pergunta = request.form['pergunta']
        if pergunta:
            resposta_gemini = call_gemini_api(pergunta)
        else:
            error = "A pergunta não pode estar vazia."
    return render_template('duvidas.html', resposta=resposta_gemini, pergunta=pergunta, error=error)


if __name__ == '__main__':
    app.run(debug=True)
