package adapters

import (
	"context"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"poptimizer/data/domain"
)

// Repo обеспечивает хранение и загрузку таблиц.
type Repo struct {
	factory domain.Factory
	uri     string
	dbName  string
	db      *mongo.Database
}

func (r *Repo) Name() string {
	return "Repo"
}

func (r *Repo) Start(ctx context.Context) error {
	client, err := mongo.Connect(ctx, options.Client().ApplyURI(r.uri))
	if err != nil {
		return err
	}

	r.db = client.Database(r.dbName)

	return nil
}

func (r *Repo) Shutdown(ctx context.Context) error {
	return r.db.Client().Disconnect(ctx)
}

// Load загружает или возвращает пустую новую таблицу.
func (r *Repo) Load(ctx context.Context, id domain.TableID) (domain.Table, error) {
	template := r.factory.NewTable(id)
	collection := r.db.Collection(string(id.Group))

	err := collection.FindOne(ctx, bson.M{"_id": id.Name}).Decode(template)
	switch {
	case err == mongo.ErrNoDocuments:
		return template, nil
	case err == nil:
		return template, nil
	default:
		return nil, err
	}
}

// ViewJOSN загружает JSON представление строк из таблицы.
func (r *Repo) ViewJOSN(ctx context.Context, id domain.TableID) ([]byte, error) {
	collection := r.db.Collection(string(id.Group))

	projections := options.FindOne().SetProjection(bson.M{"_id": 0, "rows": 1})
	raw, err := collection.FindOne(ctx, bson.M{"_id": id.Name}, projections).DecodeBytes()
	if err != nil {
		return nil, err
	}
	return bson.MarshalExtJSON(raw, true, true)
}

// Save сохраняет результаты изменения таблицы.
func (r *Repo) Save(ctx context.Context, event domain.Event) error {
	id := event.ID()
	collection := r.db.Collection(string(id.Group))

	filter := bson.M{"_id": id.Name}

	var update bson.M

	switch changes := event.(type) {
	case domain.RowsReplaced:
		update = bson.M{"$set": bson.M{"rows": changes.Rows}}
	case domain.RowsAppended:
		update = bson.M{"$push": bson.M{"rows": bson.M{"$each": changes.Rows}}}
	}

	_, err := collection.UpdateOne(ctx, filter, update, options.Update().SetUpsert(true))
	if err != nil {
		return err
	}

	return nil
}

// NewRepo - создает новое Repo.
func NewRepo(mongoURI string, mongoDB string, factory domain.Factory) *Repo {
	repo := Repo{
		uri:     mongoURI,
		dbName:  mongoDB,
		factory: factory,
	}

	return &repo
}
