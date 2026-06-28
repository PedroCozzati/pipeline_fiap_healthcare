<img align="center" style='position: fixed' width=50 src="https://github.com/PedroCozzati/pipeline_fiap_healthcare/blob/master/TrajetoSaude/frontend/public/assets/fiap.png?raw=true" />



<div align="center">
<img align="center" width=100% src="https://github.com/PedroCozzati/pipeline_fiap_healthcare/blob/master/TrajetoSaude/frontend/public/assets/trajeto-saude-logo-primary-1200px.png?raw=true" />
</div>

# <div align="center">Plataforma de Engenharia de Dados e IA para o cuidado preventivo da diabetes no trajeto urbano de São Paulo</div>

### <div align="center">TCC — <a href=https://www.fiap.com.br/mba/mba-em-engenharia-de-dados/>MBA em Engenharia de Dados</a></div>
### <div align="center"><img width=8% align="center" src="https://github.com/PedroCozzati/pipeline_fiap_healthcare/blob/master/TrajetoSaude/frontend/public/assets/fiap.png?raw=true"/> — <a href=https://www.fiap.com.br>Faculdade de Informática e Administração Paulista</a></div>
### <div align="center">Disciplina: Discovery — Case <img width=10% align="center" src="https://github.com/PedroCozzati/pipeline_fiap_healthcare/blob/master/TrajetoSaude/frontend/public/assets/Google-Logo-2015.png?raw=true"/></div>
### <div align="center">Professor orientador: Tiago Petroni Taveira</div>



>### <div align="center">Integrantes:</div>
> #### <div align="center"><a href=https://github.com/marcelabvale>Marcela Bento do Vale</a> · RM 361949</div>
>#### <div align="center"><a href=https://github.com/PedroCozzati>Pedro Henrique Cozzati Camillo</a> · RM 361284</div>
>#### <div align="center"><a href=https://github.com/NavajasThomaz>Thomaz Colalillo Navajas</a> · RM 140560</div>
>#### <div align="center"><a href=https://github.com/yamars-dev>Yasmin Martins Vasconcellos</a> · RM 363354</div>





<div align="center">
</div>



##### <div align="center"><a href=https://youtu.be>🖥️Link para Video de pitch.🖥️</a></div>


<div align="center">

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=PedroCozzati&repo=pipeline_fiap_healthcare&theme=transparent)](https://github.com/PedroCozzati/pipeline_fiap_healthcare/tree/master)

</div>


<div>
    <details open>
        <summary closed>

# Sumário</summary>

1. [Introdução](#Introdução)
2. [Instruções](#Instruções)
3. [Classificação](./notebooks/Classificação/Classificação.md)
4. [Regressão](./notebooks/Regressão/Regressão.md)
5. [Clusterização](./notebooks/Clustering/Clustering.md)
6. [Redução de Dimensionalidade](#Redução-de-Dimensionalidade)
7. [Seleção de Modelo](#Seleção-de-Modelo)
8. [Pré-processamento](#Pré-processamento)
9. [Pipelines](#Pipelines)
10. [Métricas de Avaliação](#Métricas-de-Avaliação)
11. [Utilidades](#Utilidades)
12. [Persistência de Modelo](#Persistência-de-Modelo)
13. [Datasets](#Datasets)
14. [Extensibilidade](#Extensibilidade)

    </details>
</div>

<details>
<summary>

# Introdução</summary>

### Objetivo
A template repository demonstrating best practices for project organization. Provides a structured starting point for enhanced collaboration and maintainability.

```cmd
pip install scikit-learn
```

<div align="center">
<img align="center" width=500 src="https://github.com/NavajasThomaz/RepositoryModel/blob/main/static/images/diretorios.png?raw=true" />
</div>



### Ferramentas
<div style=display:inline-block>
<img align="center" width=100 src="https://github.com/NavajasThomaz/RepositoryModel/blob/main/static/images/image.png?raw=true" />
Linguagem utilizada
</div>
<div>
<img align="center" width=100 src="https://github.com/NavajasThomaz/RepositoryModel/blob/main/static/images/image.png?raw=true" />
Biblioteca Importante.
</div>
<div>
<a href = "https://drive.google.com/"><img src="https://resources.finalsite.net/images/f_auto,q_auto,t_image_size_1/v1672955208/ccsk12inus/tmchgi8elmup78ffviev/Google_Drive_logo.png" target="_blank" width="70" align='center'></a>
Pacote completo no drive.


</div>
</details>



<details>
<summary>

# Instruções</summary>

Nessa seção está o passo a passo de como executar esse projeto em seu própio ambiente.
Nós rencomendamos montar seu ambiente utilizado o 
<a href="https://code.visualstudio.com/" target="_blank"><img src="https://img.shields.io/badge/Visual_Studio_Code-0078D4?style=for-the-badge&logo=visual%20studio%20code&logoColor=white" target="_blank"></a>

1. **Clone esse repositório**

Existem diversas formas de clonar um repositório, inclusive baixando um zip diretamente pelo navegador.

2. **Crie seu ambiente virtual**

Para o Windows basta abrir um cmd/powershell na pasta onde o repositório foi clonado e executar o seguinte comando. 

(Python 3.12.2 utilizado na criação desse projeto.)
```cmd
python -m venv venv
```
Se o ambiente tiver sido criado corretamente, basta ativa-lo  com o seguinte comando:
```cmd
venv\Scripts\activate
```
O proximo passo é instalar os pacotes/bibliotecas necessários, para isso execute o seguinte comando:
```cmd
pip install -r requirements.txt
```
Após as intalações o projeto já estará pronto para ser utilizado.
```cmd
python main.py
```
</details>
