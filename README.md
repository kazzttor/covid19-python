# Covid-19 (sistema de acompanhamento em Python)
O sistema de acompanhamento para a covid-19, escrito em Python, é um algoritmo que registra em banco de dados as informações fornecidas pelas autoridades de saúde, ou informações internas de um determinado local, com a opção de analisar essas informações matematicamente.

Este sistema foi inspirado nos dados publicados pelas autoridades de saúde no município de Diadema [disponível aqui](http://www.diadema.sp.gov.br/ss-informacoes-em-saude/25304-boletins), em São Paulo, onde os dados eram publicados, porém, sem a possibilidade de análise, já que estavam publicados no formato PDF.

Com esse sistema os dados dos relatórios são informados manualmente, retornando uma base de dados que pode ser analisada, com critérios de proporcionalidade, crescimento de casos e ir agregando informações com outras fontes de dados, como, por exemplo, o relatório de [isolamento social fornecido pelo governo do estado de São Paulo](https://www.saopaulo.sp.gov.br/coronavirus/isolamento/).

Nessa base de dados são registrados os locais, os distritos que convenciona-se como uma subdivisão desses locais, os novos casos de contágio e fatais, além das taxas de crescimento de casos e mortes, taxa de letalidade que a proporção da quantidade de mortes em função do número total de casos, taxas de ocupação de leitos e UTI, taxa de isolamento, média móvel, que é a média das sete últimas observações anteriores a data consultada, e taxa de incidência, que é a proporção de casos em função da população total do local.

A análise da média móvel consiste em comparar a média móvel com a média de 15 dias antes e determinar se há uma tendência de alta, quando a variação é positiva acima de 15%; queda, quando a variação é negativa acima de 15%; e estável, quando a variação oscilar entre -15% e +15%.

As estatísticas estão disponíveis para:

- **Distritos**: taxa de letalidade, crescimento de casos e mortes em relação ao dia anterior com análise da média móvel, crescimento dos casos e mortes em relação a semana anterior e ao mês anterior.
- **Locais**: todas as estatísticas. Taxa de letalidade, taxa de incidência, crescimento de casos, mortes e recuperados em relação ao dia anterior com análise da média móvel, crescimento dos casos, mortes e recuperados em relação a semana anterior e ao mês anterior, taxa de ocupação de UTI, taxa de ocupação de leitos, taxa de incidência, taxa de isolamento com análise da média móvel.

A análise da média móvel da taxa de isolamento é importante, pois há uma correlação inversamente proporcional entre isolamento e aumento de casos.

Este sistema tem como finalidade a análise de informações externas, além de permitir uma análise mais segmentada por bairro, em uma cidade. Pode-se por exemplo, saber como anda o espalhamento da pandemia, e traçar por meio de modelos estatísticos uma projeção da curva de casos. Também pode permitir que seja determinado se um determinado local ainda está em uma curva ascendente de casos, descendente, ou platô, quando se atingiu pico de casos e não há mais crescimento ou redução.

Existe algoritmo utiliza a versão 3 da linguagem Python, e requer as bibliotecas _SQLite_, _datetime_ e _ArgumentParser_. Este algoritmo permite que seja executável em terminal de comandos, mas pode ser acionado através do comando `python3 covid.py <conjunto de argumentos>`.

## Tarefas

- [x] Banco de dados
- [x] Cadastro de locais e distritos
- [x] Cadastro dos dados da epidemia (_incluindo vacinação - NOVO_)
- [X] Exibição do balanço
- [X] Cálculo da média móvel e análise da média móvel.
- [X] Balanço em uma determinada data e definiçao da data de registro já na linha de comando
- [X] Exclusão de balanço de uma determinada data em linha de comando
- [X] Atualizção de dados (taxa de ocupação de leitos, UTI, isolamento e vacinação) do local em linha de comando
- [ ] Interface Web (com geração de arquivos html)
- [ ] Publicação dos dados na internet via Tumblr (_experimental_)

## Para obter 

Use o comando `git` ou faça o download na [página do projeto](https://github.com/kazzttor/covid19-python)
