const { Neo4jGraphQL } = require("@neo4j/graphql");
const neo4j = require("neo4j-driver");
const { ApolloServer } = require("apollo-server");

const typeDefs = `
    type taxon {
        name: String
        rank: String
        taxid: String
        sons: [taxon] @relationship(type: "has_taxon", direction: OUT)
        cazys: [DataPoint] @cypher(statement: """
         MATCH (this) -[r:has_cazy]-> (c:cazy)
         WHERE c.name CONTAINS 'GH'
         RETURN {name: c.name, amount: r.amount}
        """)
    }

    type DataPoint {
        name: String
        amount: Int
      }

    type cazy {
        name: String
        activities: String
        clan: String
        mechanism: String
        catalytic: String
        taxons: [taxon] @relationship(type: "has_cazy", direction: IN)
        ecs: [ec] @relationship(type: "has_ec", direction: OUT)
    }

    type ec {
        name: String
        cazys: [cazy] @relationship(type: "has_ec", direction: IN)
    }


`;

const driver = neo4j.driver(
    "bolt://localhost:7687",
    neo4j.auth.basic("neo4j", "w4gn3r")
);


const neoSchema = new Neo4jGraphQL({ typeDefs, driver });
//const schema = makeAugmentedSchema({ typeDefs });


const server = new ApolloServer({
    schema: neoSchema.schema,
    //schema: schema,
    context: ({ req }) => ({ req }),
    //context: { driver }
});

server.listen(4000).then(() => console.log("Online"));