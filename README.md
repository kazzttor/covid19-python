# Covid-19 (sistema de acompanhamento em Python)
O sistema de acompanhamento para a covid-19, escrito em Python, é um algoritmo que registra em banco de dados as informações fornecidas pelas autoridades de saúde, ou informações internas de um determinado local, com a opção de analisar essas informações matematicamente.

Este sistema foi inspirado nos dados publicados pelas autoridades de saúde no município de Diadema [disponível aqui](http://www.diadema.sp.gov.br/ss-informacoes-em-saude/25304-boletins), em São Paulo, onde os dados eram publicados, porém, sem a possibilidade de análise, já que estavam publicados no formato PDF.

Com esse sistema os dados dos relatórios são informados manualmente, retornando uma base de dados que pode ser analisada, com critérios de proporcionalidade, crescimento de casos e ir agregando informações com outras fontes de dados, como, por exemplo, o relatório de [isolamento social fornecido pelo governo do estado de São Paulo](https://www.saopaulo.sp.gov.br/coronavirus/isolamento/).

Nessa base de dados são registrados os locais, os distritos que convenciona-se como uma subdivisão desses locais, os novos casos de contágio e fatais, além das taxas de crescimento de casos e mortes, taxa de letalidade que a proporção da quantidade de mortes em função do número total de casos, taxas de ocupação de leitos e UTI, taxa de isolamento, média móvel, que é a média de cinco dias de observações, sendo as duas datas anteriores e posteriores a uma determinada data, e taxa de incidência, que é a proporção de casos em função da população total do local.

As estatísticas, num primeiro momento, estão disponíveis para:

- **Distritos**: taxa de letalidade, crescimento de casos e mortes em relação ao dia anterior, crescimento dos casos e mortes em relação a semana anterior e ao mês anterior.
- **Locais**: todas as estatísticas. Taxa de letalidade, taxa de incidência, crescimento de casos, mortes e recuperados em relação ao dia anterior, crescimento dos casos, mortes e recuperados em relação a semana anterior e ao mês anterior, taxa de ocupação de UTI, taxa de ocupação de leitos, taxa de incidência, taxa de isolamento, média móvel de cinco dias anteriores à data, com data referenciada a dois dias anteriores.

Este sistema tem como finalidade a análise de informações externas, além de permitir uma análise mais segmentada por bairro, em uma cidade. Pode-se por exemplo, saber como anda o espalhamento da pandemia, e traçar por meio de modelos estatísticos uma projeção da curva de casos. Também pode permitir que seja determinado se um determinado local ainda está em uma curva ascendente de casos, descendente, ou platô, quando se atingiu pico de casos e não há mais crescimento ou redução.

Existe algoritmo utiliza a versão 3 da linguagem Python, e requer as bibliotecas _SQLite_, _datetime_ e _ArgumentParser_. Este algoritmo permite que seja executável em terminal de comandos, mas pode ser acionado através do comando `python3 covid.py <conjunto de argumentos>`.

## Tarefas

- [x] Banco de dados
- [x] Cadastro de locais e distritos
- [x] Cadastro dos dados da epidemia
- [X] Exibição do balanço (_atualizado_)
- [X] Cálculo da média móvel (_atualizado_)
- [X] Balanço em uma determinada data e definiçao da data de registro já na linha de comando
- [ ] Interface Web (em PHP)

## Para obter 

Use o comando `git` ou faça o download na [página do projeto](https://github.com/kazzttor/covid19-python)
