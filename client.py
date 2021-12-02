import requests

ip = input("Digite o IP da sua instância Django: ")
tipo = input("Digite qual request você gostaria de fazer (DELETE/POST/GET): ")


if tipo == "GET":

    response_get = requests.get('http://'+ip+':8080/tasks/all_tasks/')
    print(response_get)
    print(response_get.json())

if tipo == "POST":

    titulo = input("Digite o titulo desejado para sua task: ")
    data = input("Digite uma data de publicacao no seguinte formato (ano-mes-diaThora:minuto:segundoZ): ")
    descricao = input("Digite uma descricao para sua task: ")

    response_post = requests.post('http://'+ip+':8080/tasks/post/',
                        data={
                            'title': titulo, 
                            'pub_date': data, 
                            'description': descricao
                            }
                    )

    print(response_post)
    print(response_post.json())


if tipo == "DELETE":
    pk = input("Qual task deseja apagar? ")
    response_delete = requests.delete('http://'+ip+':8080/tasks/tasks/'+pk)
    print(response_delete)
    # print(response_delete.json())