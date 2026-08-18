from typing import Annotated

import pydantic
from faker import Faker
from mcp.server import MCPServer
from mcp.server.mcpserver import (
    AcceptedElicitation,
    CancelledElicitation,
    Context,
    DeclinedElicitation,
    Elicit,
    ElicitationResult,
    Resolve,
)

mcp = MCPServer('commerce')

fake = Faker()

class Product(pydantic.BaseModel):
    id: int
    name: str


STOCK = [
    Product(id=1, name=fake.word()),
    Product(id=2, name=fake.word()),
]

def database(product_id: int):
    for product in STOCK:
        if product.id == product_id:
            return product
    return None


class Confirm(pydantic.BaseModel):
    new_id: int | None = None


@mcp.tool()
async def get_stocks() -> list[Product]:
    """Get the current stock of products."""
    return STOCK


async def product_exists(product_id: int) -> Confirm | Elicit[Confirm]:
    """Check if a product exists in the stock."""
    product = database(product_id)
    if product is None:
        return Elicit(f"{product_id} does not exist. Choose a different ID ?", Confirm)
    return Confirm(new_id=product.id)


@mcp.tool()
async def get_stock(product_id: int, confirm: Annotated[ElicitationResult[Confirm], Resolve(product_exists)]) -> Product | None:
    """Get a specific product by its ID.

    Args:
        product_id (int): The ID of the product to retrieve.

    Returns:
        Product | None: The product if found, otherwise None.
    """
    

    product = database(product_id)

    match confirm:
        case AcceptedElicitation(data=Confirm(new_id=None)):
            return None
        case AcceptedElicitation(data=Confirm(new_id=product_id)):
            return database(product_id)
        case DeclinedElicitation():
            return "Declined product retrieval"
        case CancelledElicitation():
            return "Cancelled product retrieval"
        
    return product


@mcp.tool()
async def pay_for_product(product_id: int, ctx: Context) -> str:
    """Elicit a payment for a product.

    Args:
        product_id (int): The ID of the product to pay for.
        ctx (Context): The context for the elicitation.

    Returns:
        str | Elicit[str]: The result of the payment elicitation.
    """
    result = await ctx.elicit_url(
        message="Please complete the payment for your product.",
        url=f"https://pay.example.com/deposit/{product_id}",
        elicitation_id=f"deposit-{product_id}",
    )

    if result.action == "accept":
        return "Complete the payment in your browser."
    return "No deposit taken. The booking expires in one hour."


@mcp.tool()
async def confirm_deposit(product_id: str, ctx: Context) -> str:
    """Confirm the deposit for a product.

    Args:
        product_id (str): The ID of the product for which the deposit is being confirmed. 
        ctx (Context): The context for the elicitation.
    """
    await ctx.session.send_elicit_complete(f"deposit-{product_id}")
    return f"Deposit received for product {product_id}."


@mcp.resource("products://documentation/{product_id}")
async def product_documentation(product_id: str) -> str:
    """Get the documentation for a specific product."""
    return f"Documentation for product {product_id}"


@mcp.prompt()
async def review_product(product_id: int) -> str:
    return f"Please review the code for product {product_id}."


@mcp.resource("config://app")
async def get_config() -> str:
    """The active shop configuration."""
    return "theme=dark\nlanguage=en"


if __name__ == '__main__':
    mcp.run(transport='streamable-http', port=8002, json_response=True)
