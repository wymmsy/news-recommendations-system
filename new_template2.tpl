<!-- news_template.tpl -->
<!DOCTYPE html>
<html>
    <head>
        <link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.12/semantic.min.css">
        <script src="https://code.jquery.com/jquery-3.1.1.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.2.12/semantic.min.js"></script>
    </head>
    <body>
        <div class="ui container" style="padding-top: 10px;">
        <table class="ui celled table">
            <thead>
                <th>Title</th>
                <th>Author</th>
                <th>Complexity</th>
                <th>Предсказание</th>
                <th colspan="3">Действия</th>
            </thead>
            <tbody>
                %for row in rows:
                <tr>
                    <td><a href="{{ getattr(row, 'url', '#') }}">{{ getattr(row, 'title', 'No title') }}</a></td>
                    <td>{{ getattr(row, 'author', 'Unknown') }}</td>
                    <td>{{ getattr(row, 'complexity', '-') }}</td>
                    <td>
                        %if hasattr(row, '_label'):
                            <a href="/classify div class="ui {{ 'green' if row._label == 'good' else 'yellow' if row._label == 'maybe' else 'red' }} label">
                                {{ 'Интересно' if row._label == 'good' else 'Возможно' if row._label == 'maybe' else 'Не интересно' }}
                            </div>
                        %end
                    </td>
                    <td class="positive"><a href="/add_label/?label=good&id={{ row.id }}&redirect_url=/"classify"">Интересно</a></td>
                    <td class="active"><a href="/add_label/?label=maybe&id={{ row.id }}&redirect_url=/classify">Возможно</a></td>
                    <td class="negative"><a href="/add_label/?label=never&id={{ row.id }}&redirect_url=/classify">Не интересно</a></td>
                </tr>
                %end
            </tbody>
            <tfoot class="full-width">
                <tr>
                    <th colspan="7">
                        <a href="/update_news" class="ui right floated small primary button">Больше новостей!</a>
                        <a href="/classify" class="ui right floated small green button">Классифицировать</a>
                    </th>
                </tr>
            </tfoot>
        </table>
        </div>
    </body>
</html>