const { Neo4jGraphQL } = require("@neo4j/graphql");
const neo4j = require("neo4j-driver");
const { ApolloServer } = require("apollo-server");

const typeDefs = `
    type taxon {
        name: String
        rank: String
        taxid: String
        sons: [taxon] @relationship(type: "has_taxon", direction: OUT)
        genomes: [genome]  @cypher(statement: """
        MATCH (this) -[r1:has_taxon*1..10]-> (t:taxon) -[r2:has_genome]-> (g:genome)
        RETURN g
       """)
    }

    type genome {
        name: String
        cazys: [DataPoint] @cypher(statement: """
        MATCH (this) -[r:has_cazy]-> (c:cazy)
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
        genomes: [genome] @relationship(type: "has_cazy", direction: IN)
        ecs: [ec] @relationship(type: "has_ec", direction: OUT)
    }

    type ec {
        name: String
        cazys: [cazy] @relationship(type: "has_ec", direction: IN)
    }
`;

const driver = neo4j.driver(
    "bolt://localhost:7687",
    neo4j.auth.basic("neo4j", "[your_neo4j_password]")
);

const neoSchema = new Neo4jGraphQL({ typeDefs, driver });

const server = new ApolloServer({
    schema: neoSchema.schema,
    context: ({ req }) => ({ req }),
});

server.listen(4000).then(() => console.log("Online"));