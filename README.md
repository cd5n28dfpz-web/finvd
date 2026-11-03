# finvd.ch

Les finances publiques vaudoises en données ouvertes : un portail qui réunit, sous un même domaine, les sites de budgets et de comptes du **canton de Vaud** et de **communes vaudoises**, avec un sélecteur pour passer de l'un à l'autre.

Projet indépendant, sans lien avec l'État de Vaud ni avec les communes. Les chiffres sont ceux des documents officiels, sans commentaire.

## Fonctionnement

Chaque site (canton, commune) est publié par **son propre dépôt**, avec ses données, sa méthode et ses tests. Ce dépôt ne contient aucune donnée budgétaire : `build.py` récupère la dernière version publiée de chaque site (`site/index.html`), y ajoute

- une barre de sélection « Voir les finances de … » ;
- un préfixe pour les réglages mémorisés par le navigateur (onglet ouvert, service choisi), afin que les sites ne se mélangent pas sur le même domaine ;

puis écrit le dossier `dist/`, publié par GitHub Pages. L'assemblage se relance à chaque modification de ce dépôt et **chaque nuit**, donc une mise à jour d'un site se retrouve ici le lendemain (ou tout de suite en lançant le workflow à la main : Actions → « Assemblage et publication de finvd.ch » → Run workflow).

| Adresse | Contenu |
|---|---|
| `finvd.ch/` | Page d'accueil |
| `finvd.ch/vaud/` | [Budget vaudois](https://github.com/andant89/budget-vaud) |
| `finvd.ch/epalinges/` | [Budget d'Épalinges](https://github.com/cd5n28dfpz-web/budget-Epalinges) |

## Ajouter une commune

1. La commune a son propre dépôt public, créé sur le modèle des autres (voir le dépôt d'Épalinges), avec un fichier `site/index.html` autonome.
2. Ajouter un bloc dans `communes.json` (`id` : nom court dans l'adresse ; `nom` : libellé du sélecteur ; `depot` : `compte/dépôt` GitHub ; `description` : texte de la carte d'accueil).
3. Envoyer la modification : la commune apparaît dans le sélecteur et sur la page d'accueil.

## Essayer en local

```
python3 build.py                                  # clone les dépôts listés
python3 build.py --local vaud=/chemin/index.html  # ou utilise un fichier local pour une entité
cd dist && python3 -m http.server                 # puis http://localhost:8000
```

Si une page récupérée est vide ou trop petite, l'assemblage s'arrête sans rien publier : la version en ligne reste la précédente.

## Publication

GitHub Pages, source « GitHub Actions », domaine personnalisé `finvd.ch` (le fichier `CNAME` est produit par `build.py`). Le dépôt doit être public.

## Licence

MIT, voir [LICENSE](LICENSE). Les sites assemblés ont chacun leur licence et leurs crédits, indiqués dans leur dépôt.
