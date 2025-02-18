``` mermaid
flowchart LR
    Come[Переход на сайт] --> Login[Логин];
    Come --> Registration[Регистрация];
    Login --> Game;
    Registration --> Game;
    
    subgraph Game[Игра]
        subgraph Prepare[Подготовка]
            Shop --> Equip[Экипировка];
            Equip --> Shop[Магазин];
        end
        Prepare --> SelectMode[Выбор режима];
        SelectMode --> PvP;

        subgraph PvPFight["PvP (нет в первой версии)"]
            PvP --> Create[Создать];
            PvP --> Connect[Подключиться];
        end

        Create --> Fight[Бой];
        Connect --> Fight;

        SelectMode --> PvE;
        PvE --> SelectQuest[Выбрать квест];
        SelectQuest --> Fight;
    end
    Game --> Exit;
```
